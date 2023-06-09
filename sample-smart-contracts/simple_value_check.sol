// Reference: https://github.com/trailofbits/manticore/blob/master/examples/evm/simple_value_check.sol
// @result [{'function': 'target', 'params': {'msg.sender': 1374572960896347799916170867579510675073583002382, 'msg.value': 0}}]

contract Test {
    event Log(string);

    function target() payable public {
        if (msg.value > 10)
            emit Log("Value greater than 10");  // @target
        else
            emit Log("Value less or equal than 10");

    }

}