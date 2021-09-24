# Tokility

Toklity represents a platform that provides utility tokens. Those tokens are issued on the Algorand blockchain. This makes them digitally identifiable, which enables us to know who is, and who was, the owner of the token at any point of time. Besides the digital identification of the token, each token has associated configuration with it. The configuration defines the behavior of the token. By using smart contracts we are making sure that on every interaction with the token, we are following the rules defined in the token's configuration. With those properties, we are creating transparent playfield for all of the users on our platform. 

The utility providers, such as music bands, restaurants, airlines, conference organizers, cinemas, decide to represent their utilities as non fungible tokens on the Algorand blockchain. Then, owning a utility token means: that you have access to "Foo Fighters" concert, you have reserved a table in a restaurant, you have a seat by the window 11F from New York to Amsterdam, etc... 

By adding behavior to the tokens through various kinds of configurations, we believe that we will enable the emergence of second-hand economies. Both parties, the utility providers and the users of the tokens will benefit from this kind of economy. Usually, those utility tokens will have high demand, so the users may be able to resell them for a higher price. This reselling of the utility tokens, provides additional revenue to the utility providers.

One practical example would be: A cinema ticket, row 10 seat 2, for the premiere of the movie "Titanic" is issued as utility token. The cinema defines the initial price of the utility token for 20 euros. Additionally, they define that on every resell of the ticket they want to earn 25% of the profit while limiting the maximum resell price to be 100 euros. Some people are excited to watch the Titanic on the premiere, while some are willing to sell it if they can not make it or want to make some additional money.

# Technical solution

In order to enable the initial selling of the tickets, as well with the reselling of the tickets we needed to implement some type of decentralized exchange. Every tickets is represented as an NFT. We want all of the code logic that enables the interaction with the tickets to live on the blockchain. In order to achieve this goal, we needed to implement **only two** smart contracts: A stateful smart contract that handles all of the possible interactions with the tickets, a stateless smart contract that act as a clawback of the NFT.

## Representation of an utility token as NFT

As we said earlier, each utility token is represented as an NFT on the Algorand blockchain. We want each token to have a configurable behavior and a configurable utility. Additionally, we want all of this data to be transparent and to live on the blockchain. 

![](C:\Projects\Tokility_New\images\3.png)

The behavior configuration defines how the token will be transferred on the blockchain, while the utility configuration defines what utility the token has in the physical or the virtual world. The blockchain can not verify the properties in the utility configuration, the users need to trust the utility provider that they will provide the utilities that they said would. However, we can make sure that every transfer of the NFT follows all of the conditions that are set in the behavior configuration. This enables the utility providers to define various kinds of behaviors for their tokens.

Currently every utility provider needs to provide the following behavior configuration:

- `asa_creator` - contains the address that created the utility token. Usually every utility provider will have their own address.
- `asa_price` - defines the price that the users pay when they initially buy the token from the `asa_creator`. 
- `resell_fee` - defines how much the utility provider earns on every successful transaction on the second-hand economy.
- `maxium_sell_price` - the maximum sell price that the utility token can achieve on the second-hand economy.
- `platform_fee` - defines how much our platform receives on every successful transaction on the second-hand economy.
- `reselling_allowed` - boolean value that indicates whether the token can be sold on the second-hand economy.
- `resell_duration` - defines for how long the reselling period will last.
- `gifting_allowed` - boolean value that indicates whether one user can gift the token to another user.



