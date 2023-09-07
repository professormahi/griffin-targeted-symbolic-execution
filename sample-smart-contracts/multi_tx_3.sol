// @result [{'function': 'slitherConstructorVariables', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'bet', 'params': {'value': 0, 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}, {'function': 'bet', 'params': {'value': 0, 'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'bet', 'params': {'value': 102, 'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'check', 'params': {'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}]
pragma solidity ^0.8.0;

contract multi_tx_3 {
    uint public counter = 0;
    uint public maximum_bet = 0;

    function bet(uint value) public {
        counter += 1;
        if (value > maximum_bet)
            maximum_bet = value;
    }

    function check() public returns (uint) {
        if (counter == 3)
            return maximum_bet;  // @target maximum_bet > 100
        return 0;
    }
}
