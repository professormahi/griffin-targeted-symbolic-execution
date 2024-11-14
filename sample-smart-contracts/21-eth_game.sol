// SPDX-License-Identifier: MIT
// Reference: https://github.com/samnang/solidity-examples/blob/main/contracts/sample_apps/08_eth_game/EthGame.sol
// @heuristic state_variables_based
// @result [{'function': 'slitherConstructorVariables', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'deposit', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 1000000000000000000}}, {'function': 'deposit', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 1000000000000000000}}, {'function': 'deposit', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 1000000000000000000}}, {'function': 'deposit', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 1000000000000000000}}, {'function': 'claimReward', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'deposit', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 1000000000000000000}}]

pragma solidity ^0.8.0;

contract EthGame {
    uint256 public targetAmount = 5 ether;
    address public winner;

    uint256 public balance = 0;

    function deposit() public payable {
        require(msg.value == 1 ether, "You can only send one Ether");

        balance += msg.value;
        require(balance <= targetAmount, "Game is over");

        if (balance == targetAmount) {
            winner = msg.sender;  // @target
        }
    }

    function claimReward() public {
        require(msg.sender == winner, "Not winner");

//        (bool sent,) = msg.sender.call{value: address(this).balance}("");
//        require(sent, "Failed sending Ether");
    }
}