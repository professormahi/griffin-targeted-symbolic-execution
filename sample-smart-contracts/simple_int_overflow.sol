// Based on https://github.com/trailofbits/manticore/blob/master/examples/evm/simple_int_overflow.sol
// @result [{'function': 'slitherConstructorVariables', 'params': {}}, {'function': 'add', 'params': {'value': 65535}}, {'function': 'add', 'params': {'value': 1}}]
pragma solidity ^0.8.6;

contract Overflow {
    uint16 private sellerBalance=0;

    function add(uint16 value) public {
        sellerBalance += value; // complicated math with possible overflow

        // @target !(sellerBalance >= value)
    }
}