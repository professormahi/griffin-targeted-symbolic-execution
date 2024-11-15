// @result [{'function': 'constructor', 'params': {'msg.sender': 389733769954907444854315955391008805241582011460, 'msg.value': 0}}, {'function': 'getAdTitle', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}]

pragma solidity ^0.8.10;

contract Board {
    struct Ad {
        address owner;
        address publisher;
        string title;
    }

    address private owner;
    Ad public ad;

    constructor() {
        owner = msg.sender;
    }

    function postAd(string memory postedAdTitle) public {
        ad.owner = owner;
        ad.publisher = msg.sender;
        ad.title = postedAdTitle;
    }

    function getAdTitle() public returns (string memory) {
        require(ad.publisher == msg.sender);
        return ad.title;  // @target
    }

    function getOwner() public returns (address) {
        return owner;
    }

}