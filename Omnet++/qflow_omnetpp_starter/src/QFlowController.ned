package src;

simple QFlowController
{
    parameters:
        @class(qflowomnet::QFlowController);
        string topologyFile;
        string algorithm = default("keyaware");
        string outputCsv = default("results/qflow.csv");
        double requestRate = default(500);
        int requestLimit = default(1000);
        double fidelityThreshold = default(0.90);
        double fiberLossDbPerKm = default(0.2);
        int maxHops = default(8);
        int maxCandidatePaths = default(256);
        int srcNode = default(-1);
        int dstNode = default(-1);
        double alpha1 = default(1.0);
        double alpha2 = default(1.5);
        double alpha3 = default(0.5);
        double alpha4 = default(2.0);
        int rngSeed = default(42);
        @display("i=block/cogwheel");
}
