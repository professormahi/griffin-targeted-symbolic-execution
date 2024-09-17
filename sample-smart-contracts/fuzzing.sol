// @result [{'function': 'process', 'params': {'x': 4528, 'y': 1988, 'z': 'any', 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}]
contract fuzzing {
    function process(uint16 x, uint16 y) public returns (int)  {
        uint16 z = x * y;
        if (z == 0) {
            return - 1;
        }

        // Complex condition deep in the code
        if (x * x + y * y == 10000) {
            // Critical path that we want to test
            return 1;  // @target
        }

        return 0;
    }
}