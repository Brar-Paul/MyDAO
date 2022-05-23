from turtle import end_fill
from brownie import Token, Governance, Timelock, Treasury, accounts, config
from web3 import Web3

INITIAL_SUPPLY = Web3.toWei(1000, "ether")
EXECUTOR = accounts[0]
PROPOSER = accounts[1]
VOTER1 = accounts[2]
VOTER2 = accounts[3]
VOTER3 = accounts[4]
VOTER4 = accounts[5]
VOTER5 = accounts[6]
VOTER6 = accounts[7]
VOTER7 = accounts[8]

w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:8545"))


def deploy():
    # deploy token
    token = Token.deploy(INITIAL_SUPPLY, {"from": EXECUTOR})
    # transfer tokens to accounts
    amount = Web3.toWei(50, "ether")
    tx = token.transfer(VOTER1, amount, {"from": EXECUTOR})
    tx.wait(1)
    tx = token.transfer(VOTER2, amount, {"from": EXECUTOR})
    tx.wait(1)
    tx = token.transfer(VOTER3, amount, {"from": EXECUTOR})
    tx.wait(1)
    tx = token.transfer(VOTER4, amount, {"from": EXECUTOR})
    tx.wait(1)
    tx = token.transfer(VOTER5, amount, {"from": EXECUTOR})
    tx.wait(1)
    tx = token.transfer(VOTER6, amount, {"from": EXECUTOR})
    tx.wait(1)
    tx = token.transfer(VOTER7, amount, {"from": EXECUTOR})
    tx.wait(1)
    print(f"Token contract deployed to {token.address}")
    print("All voters have been transfered 50 tokens")

    # Deploy time lock
    min_delay = 1
    timelock = Timelock.deploy(min_delay, [PROPOSER], [EXECUTOR], {"from": EXECUTOR})
    print(f"Timelock contract deployed to {timelock.address}")

    # Deploy Governance
    governance = Governance.deploy(token.address, timelock.address, {"from": EXECUTOR})
    print(f"Governance conract deployed to {governance.address}")
    print("Setting Proposer and Executor roles")
    proposer_role = timelock.PROPOSER_ROLE()
    executor_role = timelock.EXECUTOR_ROLE()
    role_tx = timelock.grantRole(proposer_role, governance.address, {"from": EXECUTOR})
    role_tx.wait(1)
    role_tx = timelock.grantRole(executor_role, governance.address, {"from": EXECUTOR})
    role_tx.wait(1)
    print("Proposer and Executor roles granted!")

    # Deploy Treasury
    funds = Web3.toWei(50, "ether")
    treasury = Treasury.deploy(EXECUTOR, {"from": EXECUTOR})
    treasury_funding = token.transfer(treasury, funds, {"from": EXECUTOR})
    treasury_funding.wait(1)
    treasury.transferOwnership(timelock.address, {"from": EXECUTOR})
    print("All contracts deployed!!")
    return (token, governance, timelock, treasury)


# Simulate creating proposal to release funds from treasury, voting, and queing/executing


def propose(token, governance, timelock, treasury):
    # delegate voters
    # NOTICE: Clean this up with a loop later
    delegate_tx = token.delegate(VOTER1, {"from": VOTER1})
    delegate_tx.wait(1)
    delegate_tx = token.delegate(VOTER2, {"from": VOTER2})
    delegate_tx.wait(1)
    delegate_tx = token.delegate(VOTER3, {"from": VOTER3})
    delegate_tx.wait(1)
    delegate_tx = token.delegate(VOTER4, {"from": VOTER4})
    delegate_tx.wait(1)
    delegate_tx = token.delegate(VOTER5, {"from": VOTER5})
    delegate_tx.wait(1)
    delegate_tx = token.delegate(VOTER6, {"from": VOTER6})
    delegate_tx.wait(1)
    delegate_tx = token.delegate(VOTER7, {"from": VOTER7})
    delegate_tx.wait(1)
    # check treasury balance and release state of funds
    is_released = treasury.isReleased()
    print(f"Fund's released? {is_released}")
    balance = token.balanceOf(treasury)
    print(balance)
    print(f"Treasury Balance: {Web3.fromWei(balance, 'ether')} ETH")

    # create proposal
    w3_treasury = w3.eth.contract(address=treasury.address, abi=treasury.abi)
    encoded_function = w3_treasury.encodeABI("releaseFunds")
    propose_tx = governance.propose(
        [treasury.address], [0], [encoded_function], "Empty Treasury"
    )
    propose_tx.wait(1)
    receipt = propose_tx.events
    proposal_id = receipt["ProposalCreated"]["proposalId"]
    print(f"Propsal submitted, id: {proposal_id}")

    # Proposal/Snapshot info
    proposal_state = governance.state(proposal_id)
    print(f"Proposal state: {proposal_state}")
    snapshot = governance.proposalSnapshot(proposal_id)
    print(f"Proposal submitted on block # {snapshot}")
    deadline = governance.proposalDeadline(proposal_id)
    print(f"Proposal voting ends on block # {deadline}")
    blocknumber = w3.eth.get_block_number()
    print(f"Current block number: {blocknumber}")
    quorum = governance.quorum(blocknumber - 1)
    formatted_quorum = Web3.fromWei(quorum, "ether")
    print(f"Votes required to pass: {formatted_quorum}")

    # Voting (0 = against, 1 = pro, 2 = abstain)
    print("Casting votes...")
    vote = governance.castVote(proposal_id, 1, {"from": VOTER1})
    vote.wait(1)
    vote = governance.castVote(proposal_id, 1, {"from": VOTER2})
    vote.wait(1)
    vote = governance.castVote(proposal_id, 1, {"from": VOTER3})
    vote.wait(1)
    vote = governance.castVote(proposal_id, 1, {"from": VOTER4})
    vote.wait(1)
    vote = governance.castVote(proposal_id, 1, {"from": VOTER5})
    vote.wait(1)
    vote = governance.castVote(proposal_id, 1, {"from": VOTER6})
    vote.wait(1)
    vote = governance.castVote(proposal_id, 1, {"from": VOTER7})
    vote.wait(1)

    # Results

    against_votes, for_votes, abstain_votes = governance.proposalVotes(proposal_id)

    print(f"Votes for: {Web3.fromWei(for_votes, 'ether')}")
    print(f"Votes against: {Web3.fromWei(against_votes, 'ether')}")
    print(f"Votes abstained: {Web3.fromWei(abstain_votes, 'ether')}")

    proposal_state = governance.state(proposal_id)
    print(f"Proposal state: {proposal_state}")

    blocknumber = w3.eth.get_block_number()
    print(f"Current block number: {blocknumber}")

    # Queue proposal
    description_hash = Web3.keccak(text="Empty Treasury")
    queue_tx = governance.queue(
        [treasury.address],
        [0],
        [encoded_function],
        description_hash,
        {"from": EXECUTOR},
    )
    queue_tx.wait(1)
    queue_tx.wait(1)
    queue_tx.wait(1)
    proposal_state = governance.state(proposal_id)
    print(f"Proposal state: {proposal_state}")
    # Execute and confirm
    execute_tx = governance.execute(
        [treasury.address],
        [0],
        [encoded_function],
        description_hash,
        {"from": EXECUTOR},
    )
    proposal_state = governance.state(proposal_id)
    print(f"Proposal state: {proposal_state}")
    is_released = treasury.isReleased()
    print(f"Fund's released? {is_released}")
    balance = w3.eth.get_balance(treasury.address)
    print(f"Treasury Balance: {Web3.fromWei(balance, 'ether')} ETH")


def main():
    token, governance, timelock, treasury = deploy()
    propose(token, governance, timelock, treasury)
