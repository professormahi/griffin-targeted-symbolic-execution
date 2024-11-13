// Reference: https://github.com/crytic/not-so-smart-contracts/blob/master/unprotected_function/Unprotected.sol
// @result [{'function': 'constructor', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'changeOwner', 'params': {'_newOwner': 'any', 'msg.sender': 194866884977453722427157977695504402620791005730, 'msg.value': 0}}]
pragma solidity ^0.8.0;

contract Unprotected {
    address private owner;

    modifier onlyOwner {
        require(msg.sender == owner);
        _;
    }

    constructor()
    public
    {
        owner = msg.sender;
    }

    // This function should be protected
    function changeOwner(address _newOwner)
    public
    {
        // @target !(msg.sender == owner)
        owner = _newOwner;
    }

    function changeOwner_fixed(address _newOwner)
    public
    onlyOwner
    {
        owner = _newOwner;
    }
}