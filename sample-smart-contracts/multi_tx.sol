// @result [{'function': 'slitherConstructorVariables', 'params': {'msg.sender': 487167212443634306067894944238761006551977514325, 'msg.value': 0}}, {'function': 'bet', 'params': {'value': 0, 'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'bet', 'params': {'value': 0, 'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'bet', 'params': {'value': 0, 'msg.sender': 292300327466180583640736966543256603931186508595, 'msg.value': 0}}, {'function': 'bet', 'params': {'value': 0, 'msg.sender': 292300327466180583640736966543256603931186508595, 'msg.value': 0}}, {'function': 'bet', 'params': {'value': 101, 'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'check', 'params': {'msg.sender': 487167212443634306067894944238761006551977514325, 'msg.value': 0}}]
pragma solidity ^0.8.0;

contract multi_tx {
    uint public counter = 0;
    uint public maximum_bet = 0;

    function bet(uint value) public {
        counter += 1;
        if (value > maximum_bet)
            maximum_bet = value;
    }

    function check() public returns (uint) {
        if (counter == 5)
            return maximum_bet;  // @target maximum_bet > 100
        return 0;
    }
}
