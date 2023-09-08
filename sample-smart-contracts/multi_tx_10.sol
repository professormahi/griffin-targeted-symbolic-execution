
pragma solidity ^0.8.0;

contract multi_tx_10 {
    uint public counter = 0;
    uint public maximum_bid = 0;
    uint private threshold = 10;

    function bid(uint value) public {
        counter += 1;
        if (value > maximum_bid)
            maximum_bid = value;
    }

    function check() public returns (uint) {
        if (counter == threshold)
            return maximum_bid;  // @target maximum_bid > 100
        return 0;
    }
}
