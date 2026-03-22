#ifndef __QFLOWOMNET_QFLOWCONTROLLER_H
#define __QFLOWOMNET_QFLOWCONTROLLER_H

#include <omnetpp.h>
#include <vector>
#include <string>
#include <unordered_map>
#include <fstream>
#include <random>

using namespace omnetpp;

namespace qflowomnet {

struct EdgeState {
    int src = -1;
    int dst = -1;
    double distanceKm = 0.0;
    double baseKeyRate = 5000.0;
    double coherenceMs = 50.0;
    double qber = 0.03;
    int keyCount = 0;
    double avgFidelity = 0.97;
    int consumedKeys = 0;
    double generatedKeysTotal = 0.0;
};

struct PathMetrics {
    bool feasible = false;
    std::vector<int> path;
    int hops = 0;
    double totalDistanceKm = 0.0;
    double totalCompositeCost = 0.0;
    double bottleneckFidelity = 0.0;
    double maxUtilization = 0.0;
    int keysConsumed = 0;
};

class QFlowController : public cSimpleModule
{
  private:
    cMessage *nextRequestEvent = nullptr;
    std::vector<EdgeState> edges;
    std::unordered_map<long long, int> edgeIndex;
    int nodeCount = 0;
    double currentTimeS = 0.0;
    long requestCounter = 0;
    long blockedCounter = 0;
    long servedCounter = 0;
    std::ofstream csv;
    std::mt19937_64 rng;

    std::string topologyFile;
    std::string algorithm;
    std::string outputCsv;

    double requestRate = 1000.0;
    long requestLimit = 1000;
    double fidelityThreshold = 0.90;
    double fiberLossDbPerKm = 0.2;
    int maxHops = 8;
    int maxCandidatePaths = 256;
    int fixedSrc = -1;
    int fixedDst = -1;

    double alpha1 = 1.0;
    double alpha2 = 1.5;
    double alpha3 = 0.5;
    double alpha4 = 2.0;

  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    virtual void finish() override;

    void loadTopologyCsv(const std::string& path);
    void advanceLinkStates(double dtS);
    void processOneRequest();
    void writeCsvHeader();
    void logRequest(const PathMetrics& pm, int src, int dst, double decisionLatencyMs);

    long long edgeKey(int u, int v) const;
    bool hasEdge(int u, int v) const;
    EdgeState& getEdge(int u, int v);
    const EdgeState& getEdgeConst(int u, int v) const;
    std::vector<int> neighbors(int u) const;

    double effectiveArrivalRate(const EdgeState& e) const;
    double compositeWeight(const EdgeState& e) const;
    double utilization(const EdgeState& e) const;

    PathMetrics evaluatePath(const std::vector<int>& path) const;
    PathMetrics runDistanceDijkstra(int src, int dst) const;
    PathMetrics runKeyAwareDijkstra(int src, int dst) const;
    PathMetrics runRandomPath(int src, int dst);
    PathMetrics runGaTchebyProxy(int src, int dst);
    void enumerateSimplePaths(int current, int dst, std::vector<int>& curPath, std::vector<int>& visited,
                              std::vector<std::vector<int>>& outPaths);

    std::pair<int,int> pickRequestEndpoints();
    double sampleExponential(double ratePerS);
    int samplePoisson(double mean);
};

} // namespace qflowomnet

#endif
