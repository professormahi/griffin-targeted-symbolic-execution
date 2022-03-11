pragma solidity ^0.8.6;

contract Overflow {
    uint private sellerBalance = 0;

    function add(uint value) public {
        sellerBalance += value;
        // complicated math with possible overflow

        // possible auditor assert
        assert(sellerBalance >= value);
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
