// SPDX-License-Identifier: MIT
// Reference: https://github.com/samnang/solidity-examples/blob/main/contracts/sample_apps/02_address_book/AddressBook.sol
// @result [{'function': 'addContact', 'params': {'index': 292300327466180583640736966543256603931186508595, 'contact': 0, 'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}]

pragma solidity ^0.8.0;

contract AddressBook {
    address[] private contacts;

    function getContacts() public view returns (address[] memory) {
        return contacts;
    }

    function addContact(uint index, address contact) public {
        contacts[index] = contact;  // @target
    }
}