// Reference: https://github.com/trailofbits/manticore/blob/master/examples/evm/simple_int_overflow.sol
// @result [{'function': 'slitherConstructorVariables', 'params': {'msg.sender': 1428138688462619281669692826666878014146355723359, 'msg.value': 0}}, {'function': 'add', 'params': {'value': 65535, 'msg.sender': 1428138688462619281669692826666878014146355723359, 'msg.value': 0}}, {'function': 'add', 'params': {'value': 1, 'msg.sender': 520131281686628808547020524492327816004763095176, 'msg.value': 0}}]
pragma solidity ^0.8.6;

contract Overflow {
    uint16 private sellerBalance=0;

    function add(uint16 value) public {
        sellerBalance += value; // complicated math with possible overflow

        // @target !(sellerBalance >= value)
    }
}