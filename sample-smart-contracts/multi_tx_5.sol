// @result [{'function': 'slitherConstructorVariables', 'params': {'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}, {'function': 'bid', 'params': {'value': 0, 'msg.sender': 292300327466180583640736966543256603931186508595, 'msg.value': 0}}, {'function': 'bid', 'params': {'value': 0, 'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'bid', 'params': {'value': 0, 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}, {'function': 'bid', 'params': {'value': 0, 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}, {'function': 'bid', 'params': {'value': 101, 'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'check', 'params': {'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}]
pragma solidity ^0.8.0;

contract multi_tx_5 {
    uint public counter = 0;
    uint public maximum_bid = 0;
    uint private threshold = 5;

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
