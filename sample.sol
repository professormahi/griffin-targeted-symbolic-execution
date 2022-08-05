pragma solidity ^0.8.6;

contract Overflow {
    uint private sellerBalance = 0;

    function add(uint value) public {
        sellerBalance += value;
        // complicated math with possible overflow

        // possible auditor assert
        assert(sellerBalance >= value);
    }

    function compute(uint input) public returns (uint){
        uint result = input;

        for (uint i; i < 100; i++)
            result += i;

        if (result == 150) {
            return result;
        } else {
            return 0;
        }
    }

    function reset() public {
        sellerBalance = 0;
    }

    function is_zero() public view returns (bool) {
        if (sellerBalance == 0)
            return true;

        return false;
    }
}
