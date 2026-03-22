#include "QFlowController.h"
#include <fstream>
#include <sstream>
#include <queue>
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <limits>

namespace qflowomnet {

Define_Module(QFlowController);

long long QFlowController::edgeKey(int u, int v) const {
    return (static_cast<long long>(u) << 32) ^ static_cast<unsigned int>(v);
}

bool QFlowController::hasEdge(int u, int v) const {
    return edgeIndex.find(edgeKey(u, v)) != edgeIndex.end();
}

EdgeState& QFlowController::getEdge(int u, int v) {
    return edges.at(edgeIndex.at(edgeKey(u, v)));
}

const EdgeState& QFlowController::getEdgeConst(int u, int v) const {
    return edges.at(edgeIndex.at(edgeKey(u, v)));
}

std::vector<int> QFlowController::neighbors(int u) const {
    std::vector<int> out;
    for (const auto& e : edges) {
        if (e.src == u)
            out.push_back(e.dst);
    }
    std::sort(out.begin(), out.end());
    return out;
}

double QFlowController::effectiveArrivalRate(const EdgeState& e) const {
    double lossDb = fiberLossDbPerKm * e.distanceKm;
    return e.baseKeyRate * std::pow(10.0, -lossDb / 10.0);
}

double QFlowController::compositeWeight(const EdgeState& e) const {
    if (e.keyCount < 1 || e.avgFidelity < fidelityThreshold)
        return std::numeric_limits<double>::infinity();
    double lambdaEff = std::max(1e-9, effectiveArrivalRate(e));
    double k = std::max(1, e.keyCount);
    double f = std::max(1e-6, e.avgFidelity);
    return alpha1 / k + alpha2 / f + alpha3 / lambdaEff + alpha4 * e.qber;
}

double QFlowController::utilization(const EdgeState& e) const {
    double denom = std::max(1, e.keyCount + e.consumedKeys);
    return static_cast<double>(e.consumedKeys) / denom;
}

double QFlowController::sampleExponential(double ratePerS) {
    if (ratePerS <= 0) return 1e9;
    std::exponential_distribution<double> d(ratePerS);
    return d(rng);
}

int QFlowController::samplePoisson(double mean) {
    if (mean <= 0) return 0;
    std::poisson_distribution<int> d(mean);
    return d(rng);
}

void QFlowController::loadTopologyCsv(const std::string& path) {
    std::ifstream fin(path);
    if (!fin.is_open())
        throw cRuntimeError("Could not open topology CSV: %s", path.c_str());

    edges.clear();
    edgeIndex.clear();
    nodeCount = 0;

    std::string line;
    while (std::getline(fin, line)) {
        if (line.empty() || line[0] == '#')
            continue;
        std::stringstream ss(line);
        std::string tok;
        std::vector<std::string> toks;
        while (std::getline(ss, tok, ',')) toks.push_back(tok);
        if (toks.size() < 6)
            continue;

        EdgeState e;
        e.src = std::stoi(toks[0]);
        e.dst = std::stoi(toks[1]);
        e.distanceKm = std::stod(toks[2]);
        e.baseKeyRate = std::stod(toks[3]);
        e.coherenceMs = std::stod(toks[4]);
        e.qber = std::stod(toks[5]);
        e.keyCount = 10;
        e.avgFidelity = std::max(0.0, 1.0 - e.qber);
        int idx = edges.size();
        edges.push_back(e);
        edgeIndex[edgeKey(e.src, e.dst)] = idx;
        nodeCount = std::max(nodeCount, std::max(e.src, e.dst) + 1);
    }

    if (edges.empty())
        throw cRuntimeError("Topology CSV loaded zero edges: %s", path.c_str());
}

void QFlowController::advanceLinkStates(double dtS) {
    const int MAX_KEY_POOL = 128;

    for (auto& e : edges) {
        int oldKeys = e.keyCount;

        // New key generation
        int newKeys = samplePoisson(effectiveArrivalRate(e) * dtS);
        double newKeyFid = std::max(0.0, 1.0 - e.qber);

        // Coherence-driven survival of existing keys
        double tauS = std::max(1e-6, e.coherenceMs / 1000.0);
        double survival = std::exp(-dtS / tauS);

        // Surviving old key count
        int survivingOldKeys = static_cast<int>(std::round(oldKeys * survival));
        if (survivingOldKeys < 0) survivingOldKeys = 0;

        // Old-key fidelity also decays
        double decayedOldFid = e.avgFidelity * survival;
        if (decayedOldFid < 0.0) decayedOldFid = 0.0;

        // Mix surviving old keys and new keys
        int totalKeys = survivingOldKeys + newKeys;
        if (totalKeys > MAX_KEY_POOL) {
            // keep the freshest keys preferentially
            int overflow = totalKeys - MAX_KEY_POOL;

            if (survivingOldKeys >= overflow) {
                survivingOldKeys -= overflow;
            } else {
                overflow -= survivingOldKeys;
                survivingOldKeys = 0;
                newKeys = std::max(0, newKeys - overflow);
            }

            totalKeys = survivingOldKeys + newKeys;
        }

        if (totalKeys > 0) {
            double weightedSum =
                decayedOldFid * survivingOldKeys +
                newKeyFid * newKeys;
            e.avgFidelity = weightedSum / totalKeys;
        } else {
            e.avgFidelity = newKeyFid;
        }

        e.keyCount = totalKeys;
        e.generatedKeysTotal += newKeys;

        // If fidelity is far below threshold, flush the stale pool aggressively
        if (e.avgFidelity < 0.8 * fidelityThreshold) {
            e.keyCount = static_cast<int>(0.5 * e.keyCount);
            if (e.keyCount < 0) e.keyCount = 0;
        }
    }
}
PathMetrics QFlowController::evaluatePath(const std::vector<int>& path) const {
    PathMetrics pm;
    pm.path = path;
    pm.hops = (path.size() >= 2) ? static_cast<int>(path.size()) - 1 : 0;
    pm.bottleneckFidelity = std::numeric_limits<double>::infinity();
    pm.feasible = !path.empty() && path.size() >= 2;

    if (!pm.feasible)
        return pm;

    for (size_t i = 0; i + 1 < path.size(); ++i) {
        int u = path[i], v = path[i + 1];
        if (!hasEdge(u, v)) {
            pm.feasible = false;
            return pm;
        }
        const auto& e = getEdgeConst(u, v);
        if (e.keyCount < 1 || e.avgFidelity < fidelityThreshold) {
            pm.feasible = false;
            return pm;
        }
        pm.totalDistanceKm += e.distanceKm;
        pm.totalCompositeCost += compositeWeight(e);
        pm.bottleneckFidelity = std::min(pm.bottleneckFidelity, e.avgFidelity);
        pm.maxUtilization = std::max(pm.maxUtilization, utilization(e));
        pm.keysConsumed += 1;
    }

    if (pm.bottleneckFidelity == std::numeric_limits<double>::infinity())
        pm.bottleneckFidelity = 0.0;

    return pm;
}

PathMetrics QFlowController::runDistanceDijkstra(int src, int dst) const {
    const double INF = 1e100;
    std::vector<double> dist(nodeCount, INF);
    std::vector<int> parent(nodeCount, -1);
    using Node = std::pair<double, int>;
    std::priority_queue<Node, std::vector<Node>, std::greater<Node>> pq;

    dist[src] = 0.0;
    pq.push({0.0, src});

    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();
        if (d != dist[u]) continue;
        if (u == dst) break;

        for (int v : neighbors(u)) {
            const auto& e = getEdgeConst(u, v);
            if (e.keyCount < 1 || e.avgFidelity < fidelityThreshold) continue;
            double w = e.distanceKm;
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                parent[v] = u;
                pq.push({dist[v], v});
            }
        }
    }

    if (parent[dst] == -1) return PathMetrics{};
    std::vector<int> path;
    for (int cur = dst; cur != -1; cur = parent[cur]) path.push_back(cur);
    std::reverse(path.begin(), path.end());
    return evaluatePath(path);
}

PathMetrics QFlowController::runKeyAwareDijkstra(int src, int dst) const {
    const double INF = 1e100;
    std::vector<double> dist(nodeCount, INF);
    std::vector<int> parent(nodeCount, -1);
    using Node = std::pair<double, int>;
    std::priority_queue<Node, std::vector<Node>, std::greater<Node>> pq;

    dist[src] = 0.0;
    pq.push({0.0, src});

    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();
        if (d != dist[u]) continue;
        if (u == dst) break;

        for (int v : neighbors(u)) {
            const auto& e = getEdgeConst(u, v);
            double w = compositeWeight(e);
            if (!std::isfinite(w)) continue;
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                parent[v] = u;
                pq.push({dist[v], v});
            }
        }
    }

    if (parent[dst] == -1) return PathMetrics{};
    std::vector<int> path;
    for (int cur = dst; cur != -1; cur = parent[cur]) path.push_back(cur);
    std::reverse(path.begin(), path.end());
    return evaluatePath(path);
}

void QFlowController::enumerateSimplePaths(int current, int dst, std::vector<int>& curPath,
                                           std::vector<int>& visited,
                                           std::vector<std::vector<int>>& outPaths) {
    if ((int)outPaths.size() >= maxCandidatePaths)
        return;
    if ((int)curPath.size() > maxHops)
        return;
    if (current == dst) {
        outPaths.push_back(curPath);
        return;
    }

    auto nbrs = neighbors(current);
    std::shuffle(nbrs.begin(), nbrs.end(), rng);

    for (int nxt : nbrs) {
        if (visited[nxt]) continue;
        if (!hasEdge(current, nxt)) continue;
        const auto& e = getEdgeConst(current, nxt);
        if (e.keyCount < 1 || e.avgFidelity < fidelityThreshold) continue;

        visited[nxt] = 1;
        curPath.push_back(nxt);
        enumerateSimplePaths(nxt, dst, curPath, visited, outPaths);
        curPath.pop_back();
        visited[nxt] = 0;

        if ((int)outPaths.size() >= maxCandidatePaths)
            return;
    }
}

PathMetrics QFlowController::runRandomPath(int src, int dst) {
    std::vector<int> visited(nodeCount, 0);
    std::vector<std::vector<int>> candidates;
    std::vector<int> cur{src};
    visited[src] = 1;
    enumerateSimplePaths(src, dst, cur, visited, candidates);
    if (candidates.empty()) return PathMetrics{};
    std::uniform_int_distribution<int> pick(0, (int)candidates.size() - 1);
    return evaluatePath(candidates[pick(rng)]);
}

PathMetrics QFlowController::runGaTchebyProxy(int src, int dst) {
    std::vector<int> visited(nodeCount, 0);
    std::vector<std::vector<int>> candidates;
    std::vector<int> cur{src};
    visited[src] = 1;
    enumerateSimplePaths(src, dst, cur, visited, candidates);
    if (candidates.empty()) return PathMetrics{};

    std::vector<PathMetrics> evals;
    evals.reserve(candidates.size());
    for (const auto& p : candidates) {
        auto pm = evaluatePath(p);
        if (pm.feasible)
            evals.push_back(pm);
    }
    if (evals.empty()) return PathMetrics{};

    double idealLatency = 1e100;
    double idealLoad = 1e100;
    double idealNegFid = 1e100;

    for (const auto& pm : evals) {
        idealLatency = std::min(idealLatency, pm.totalCompositeCost);
        idealLoad = std::min(idealLoad, pm.maxUtilization);
        idealNegFid = std::min(idealNegFid, -pm.bottleneckFidelity);
    }

    double w1 = 0.4, w2 = 0.4, w3 = 0.2;
    double bestScore = 1e100;
    int bestIdx = -1;
    for (size_t i = 0; i < evals.size(); ++i) {
        const auto& pm = evals[i];
        double f1 = pm.totalCompositeCost;
        double f2 = -pm.bottleneckFidelity;
        double f3 = pm.maxUtilization;
        double score = std::max({w1 * std::abs(f1 - idealLatency),
                                 w2 * std::abs(f2 - idealNegFid),
                                 w3 * std::abs(f3 - idealLoad)});
        if (score < bestScore) {
            bestScore = score;
            bestIdx = (int)i;
        }
    }

    if (bestIdx < 0) return PathMetrics{};
    return evals[bestIdx];
}

std::pair<int,int> QFlowController::pickRequestEndpoints() {
    if (fixedSrc >= 0 && fixedDst >= 0 && fixedSrc != fixedDst)
        return {fixedSrc, fixedDst};

    std::uniform_int_distribution<int> dist(0, nodeCount - 1);
    int s = dist(rng), d = dist(rng);
    while (d == s) d = dist(rng);
    return {s, d};
}

void QFlowController::writeCsvHeader() {
    csv << "request_id,time_s,algorithm,topology,src,dst,blocked,path,hops,distance_km,"
           "composite_cost,bottleneck_fidelity,max_utilization,keys_consumed,decision_latency_ms,served_total,blocked_total\n";
}

void QFlowController::logRequest(const PathMetrics& pm, int src, int dst, double decisionLatencyMs) {
    std::stringstream pathSs;
    if (pm.path.empty()) pathSs << "[]";
    else {
        pathSs << "[";
        for (size_t i = 0; i < pm.path.size(); ++i) {
            if (i) pathSs << "-";
            pathSs << pm.path[i];
        }
        pathSs << "]";
    }

    std::filesystem::path topoPath(topologyFile);

    csv << requestCounter << ","
        << currentTimeS << ","
        << algorithm << ","
        << topoPath.stem().string() << ","
        << src << "," << dst << ","
        << (pm.feasible ? 0 : 1) << ","
        << "\"" << pathSs.str() << "\"" << ","
        << pm.hops << ","
        << pm.totalDistanceKm << ","
        << pm.totalCompositeCost << ","
        << pm.bottleneckFidelity << ","
        << pm.maxUtilization << ","
        << pm.keysConsumed << ","
        << decisionLatencyMs << ","
        << servedCounter << ","
        << blockedCounter
        << "\n";
}

void QFlowController::processOneRequest() {
    auto [srcNode, dstNode] = pickRequestEndpoints();

    PathMetrics pm;
    if (algorithm == "distance")
        pm = runDistanceDijkstra(srcNode, dstNode);
    else if (algorithm == "keyaware")
        pm = runKeyAwareDijkstra(srcNode, dstNode);
    else if (algorithm == "random")
        pm = runRandomPath(srcNode, dstNode);
    else if (algorithm == "ga_tcheby_proxy")
        pm = runGaTchebyProxy(srcNode, dstNode);
    else
        throw cRuntimeError("Unknown algorithm: %s", algorithm.c_str());

    double decisionLatencyMs = 0.0;
    if (algorithm == "distance") decisionLatencyMs = 0.02;
    else if (algorithm == "keyaware") decisionLatencyMs = 0.05;
    else if (algorithm == "random") decisionLatencyMs = 0.01;
    else if (algorithm == "ga_tcheby_proxy") decisionLatencyMs = 0.50;

    if (pm.feasible) {
        servedCounter++;
        for (size_t i = 0; i + 1 < pm.path.size(); ++i) {
            auto& e = getEdge(pm.path[i], pm.path[i + 1]);
            if (e.keyCount > 0) e.keyCount -= 1;
            e.consumedKeys += 1;
        }
    } else {
        blockedCounter++;
    }

    logRequest(pm, srcNode, dstNode, decisionLatencyMs);
}

void QFlowController::initialize() {
    topologyFile = par("topologyFile").stdstringValue();
    algorithm = par("algorithm").stdstringValue();
    outputCsv = par("outputCsv").stdstringValue();
    requestRate = par("requestRate").doubleValue();
    requestLimit = static_cast<long>(par("requestLimit").intValue());
    fidelityThreshold = par("fidelityThreshold").doubleValue();
    fiberLossDbPerKm = par("fiberLossDbPerKm").doubleValue();
    maxHops = par("maxHops").intValue();
    maxCandidatePaths = par("maxCandidatePaths").intValue();
    fixedSrc = par("srcNode").intValue();
    fixedDst = par("dstNode").intValue();
    alpha1 = par("alpha1").doubleValue();
    alpha2 = par("alpha2").doubleValue();
    alpha3 = par("alpha3").doubleValue();
    alpha4 = par("alpha4").doubleValue();

    int seed = par("rngSeed").intValue();
    rng.seed(seed);

    loadTopologyCsv(topologyFile);

    std::filesystem::path outPath(outputCsv);
    if (outPath.has_parent_path())
        std::filesystem::create_directories(outPath.parent_path());
    csv.open(outputCsv);
    if (!csv.is_open())
        throw cRuntimeError("Could not open CSV output: %s", outputCsv.c_str());
    writeCsvHeader();

    requestCounter = 0;
    blockedCounter = 0;
    servedCounter = 0;
    currentTimeS = 0.0;

    nextRequestEvent = new cMessage("nextRequest");
    scheduleAt(simTime() + sampleExponential(requestRate), nextRequestEvent);
}

void QFlowController::handleMessage(cMessage *msg) {
    if (msg != nextRequestEvent)
        throw cRuntimeError("Unexpected message");

    double newTimeS = simTime().dbl();
    double dtS = std::max(0.0, newTimeS - currentTimeS);
    advanceLinkStates(dtS);
    currentTimeS = newTimeS;

    processOneRequest();
    requestCounter++;

    if (requestCounter >= requestLimit) {
        endSimulation();
        return;
    }

    scheduleAt(simTime() + sampleExponential(requestRate), nextRequestEvent);
}

void QFlowController::finish() {
    if (nextRequestEvent) {
        cancelAndDelete(nextRequestEvent);
        nextRequestEvent = nullptr;
    }

    if (csv.is_open()) {
        csv.flush();
        csv.close();
    }

    recordScalar("requests_total", requestCounter);
    recordScalar("requests_served", servedCounter);
    recordScalar("requests_blocked", blockedCounter);
    recordScalar("blocking_probability", requestCounter > 0 ? (double)blockedCounter / requestCounter : 0.0);
}

} // namespace qflowomnet
