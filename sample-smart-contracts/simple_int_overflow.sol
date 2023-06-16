// Reference: https://github.com/trailofbits/manticore/blob/master/examples/evm/simple_int_overflow.sol
// @result [{'function': 'slitherConstructorVariables', 'params': {'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'add', 'params': {'value': 65535, 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}, {'function': 'add', 'params': {'value': 1, 'msg.sender': 292300327466180583640736966543256603931186508595, 'msg.value': 0}}]
pragma solidity ^0.8.6;

contract Overflow {
    uint16 private sellerBalance=0;

    function add(uint16 value) public {
        sellerBalance += value; // complicated math with possible overflow

        // @target !(sellerBalance >= value)
    }
}