
pragma solidity ^0.8.0;

contract multi_tx_10 {
    uint public counter = 0;
    uint public maximum_bet = 0;

    function bet(uint value) public {
        counter += 1;
        if (value > maximum_bet)
            maximum_bet = value;
    }

    function check() public returns (uint) {
        if (counter == 10)
            return maximum_bet;  // @target maximum_bet > 100
        return 0;
    }
}
