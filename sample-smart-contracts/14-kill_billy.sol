// Reference: https://github.com/Consensys/mythril/blob/develop/solidity_examples/killbilly.sol
// @heuristic state_variables_based
// @result: [{'function': 'constructor', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'killerize', 'params': {'addr': 97433442488726861213578988847752201310395502865, 'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'activateKillability', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'commenceKilling', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}]

pragma solidity ^0.8.0;

contract KillBilly {
    bool public is_killable;
    address private approved_killer;

    constructor() {
        is_killable = false;
    }

    function killerize(address addr) public {
        approved_killer = addr;
    }

    function activateKillability() public {
        require(approved_killer == msg.sender);
        is_killable = true;
    }

    function commenceKilling() public {
        require(is_killable); // @target
        selfdestruct(payable(msg.sender));
    }
}