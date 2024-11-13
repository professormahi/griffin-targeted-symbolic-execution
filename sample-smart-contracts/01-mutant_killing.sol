// @result [{'function': 'check', 'params': {'a': 160, 'b': 160, 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}]
pragma solidity ^0.8.0;

contract mutant_killing {
    function check(uint8 a, uint8 b) public returns (bool) {
        if (a >= b)  // Original: `a > b`
            return true;  // @target !(a > b)
        return false;
    }
}
