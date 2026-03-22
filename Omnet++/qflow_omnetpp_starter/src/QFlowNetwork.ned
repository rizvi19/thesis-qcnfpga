package src;

network QFlowNetwork
{
    parameters:
        @display("bgb=600,300");
    submodules:
        controller: QFlowController {
            @display("p=300,150");
        }
}
