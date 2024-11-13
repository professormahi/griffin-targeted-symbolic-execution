// Reference: https://github.com/trailofbits/manticore/blob/master/examples/evm/simple_value_check.sol
// @result [{'function': 'target', 'params': {'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}]

contract SimpleMsgValueCheck {
    event Log(string);

    function target() payable public {
        if (msg.value > 10)
            emit Log("Value greater than 10");  // @target
        else
            emit Log("Value less or equal than 10");

    }

}