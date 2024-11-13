// Reference: https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/math/Math.sol
// @result [{'function': 'log10', 'params': {'value': 13164087656369971425368478026478388781562443983090358895392063488, 'result': 'any', 'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}]

pragma solidity ^0.8.0;

contract log_test {
     function log10(uint256 value) public returns (uint256) {
        uint256 result = 0;
        unchecked {
            if (value >= 10000000000000000000000000000000000000000000000000000000000000000) {
                value /= 10000000000000000000000000000000000000000000000000000000000000000;
                result += 64;  // @target value == 1
            }
            if (value >= 100000000000000000000000000000000) {
                value /= 100000000000000000000000000000000;
                result += 32;
            }
            if (value >= 10000000000000000) {
                value /= 10000000000000000;
                result += 16;
            }
            if (value >= 100000000) {
                value /= 100000000;
                result += 8;
            }
            if (value >= 10000) {
                value /= 10000;
                result += 4;
            }
            if (value >= 100) {
                value /= 100;
                result += 2;
            }
            if (value >= 10) {
                result += 1;
            }
        }
        return result;
    }

    function average(uint256 a, uint256 b) public returns (uint256) {
        // (a + b) / 2 can overflow.
        return (a & b) + (a ^ b) / 2;
    }

    function bool_to_uint(bool expr) internal returns (uint256 u)  {
        assembly {
            u := iszero(iszero(expr))
        }
    }

    function ternary(bool condition, uint256 a, uint256 b) public returns (uint256) {
        unchecked {
            // branchless ternary works because:
            // b ^ (a ^ b) == a
            // b ^ 0 == b
            return b ^ ((a ^ b) * bool_to_uint(condition));
        }
    }

    function max(uint256 a, uint256 b) public returns (uint256) {
        return ternary(a > b, a, b);
    }

    function min(uint256 a, uint256 b) public returns (uint256) {
        return ternary(a < b, a, b);
    }
}