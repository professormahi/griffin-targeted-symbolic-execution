// Reference: https://github.com/crytic/not-so-smart-contracts/blob/master/unprotected_function/Unprotected.sol
// @result [{'function': 'constructor', 'params': {'msg.sender': 487167212443634306067894944238761006551977514325, 'msg.value': 0}}, {'function': 'changeOwner', 'params': {'_newOwner': 'any', 'msg.sender': 292300327466180583640736966543256603931186508595, 'msg.value': 0}}]
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