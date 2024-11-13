// Reference: https://github.com/samnang/solidity-examples/blob/main/contracts/sample_apps/06_shared_wallet/SharedWallet.sol
// @result [{'function': 'constructor', 'params': {'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}, {'function': 'withdraw', 'params': {'amount': 0, 'msg.sender': 97433442488726861213578988847752201310395502865, 'msg.value': 0}}]

pragma solidity ^0.8.0;

contract SharedWallet {
    address private _owner;

    event DepositFunds(address from, uint256 amount);
    event WithdrawFunds(address from, uint256 amount);
    event TransferFunds(address from, address to, uint256 amount);

    constructor() {
        _owner = msg.sender;
    }

    // receive the deposit into shared wallet (contract's balance)
    receive() external payable {
        emit DepositFunds(msg.sender, msg.value);
    }

    // withdraw fund from the shared wallet into the signer of transaction
    function withdraw(uint256 amount) public {
        require(msg.sender == _owner);
        require(address(this).balance >= amount);  // @target
        payable(msg.sender).transfer(amount);
        emit WithdrawFunds(msg.sender, amount);
    }

    // transfer fund from the shared wallet into another address
    function transferTo(address payable to, uint256 amount) public {
        require(msg.sender == _owner);
        require(address(this).balance >= amount);
        payable(to).transfer(amount);
        emit TransferFunds(msg.sender, to, amount);
    }
}