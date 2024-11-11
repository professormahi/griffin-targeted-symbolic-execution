// Reference: https://github.com/trailofbits/manticore/blob/master/examples/evm/simple_value_check.sol
// @result [{'function': 'target', 'params': {'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}]

contract SimpleMsgValueCheck {
    event Log(string);

    function target() payable public {
        if (msg.value > 10)
            emit Log("Value greater than 10");  // @target
        else
            emit Log("Value less or equal than 10");

    }

}