// Reference: https://github.com/trailofbits/manticore/blob/master/examples/evm/simple_int_overflow.sol
// @result [{'function': 'slitherConstructorVariables', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'add', 'params': {'value': 65535, 'msg.sender': 487167212443634306067894944238761006551977514325, 'msg.value': 0}}, {'function': 'add', 'params': {'value': 1, 'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}]
pragma solidity ^0.8.6;

contract Overflow {
    uint16 private sellerBalance=0;

    function add(uint16 value) public {
        sellerBalance += value; // complicated math with possible overflow

        // @target !(sellerBalance >= value)
    }
}