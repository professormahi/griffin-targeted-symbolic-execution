// Reference: https://github.com/trailofbits/manticore/blob/master/examples/evm/simple_value_check.sol
// @result [{'function': 'constructor', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'target', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 10}}]

contract SimpleMsgValueCheck {
    event Log(string);

    uint256 public value;

    constructor() {
        value = 0;
    }

    function target() payable public {
        if (msg.value >= 10) {
            value = msg.value;
            emit Log("Value greater than 10");  // @target (value >= 10) && !(value > 10)
        } else {
            value = msg.value;
            emit Log("Value less or equal than 10");
        }

    }

}