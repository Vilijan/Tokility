# Tokility

Toklity represents a platform that provides utility tokens. Those tokens are issued on the Algorand blockchain. This makes them digitally identifiable, which enables us to know who is, and who was, the owner of the token at any point of time. Besides the digital identification of the token, each token has associated configuration with it. The configuration defines the behavior of the token. By using smart contracts we are making sure that on every interaction with the token, we are following the rules defined in the token's configuration. With those properties, we are creating transparent playfield for all of the users on our platform. 

The utility providers, such as music bands, restaurants, airlines, conference organizers, cinemas, decide to represent their utilities as non fungible tokens on the Algorand blockchain. Then, owning a utility token means: that you have access to "Foo Fighters" concert, you have reserved a table in a restaurant, you have a seat by the window 11F from New York to Amsterdam, etc... 

By adding behavior to the tokens through various kinds of configurations, we believe that we will enable the emergence of second-hand economies. Both parties, the utility providers and the users of the tokens will benefit from this kind of economy. Usually, those utility tokens will have high demand, so the users may be able to resell them for a higher price. This reselling of the utility tokens, provides additional revenue to the utility providers.

# Technical explanation

In order to enable the initial selling of the tickets, as well with the reselling of the tickets we needed to implement some type of decentralized exchange. Every tickets is represented as an NFT. We want all of the code logic that enables the interaction with the tickets to live on the blockchain. In order to achieve this goal, we needed to implement **only two** smart contracts: A stateful smart contract that handles all of the possible interactions with the tickets, and a stateless smart contract that act as a clawback of the NFT.

## Representation of an utility token as NFT

As we said earlier, each utility token is represented as an NFT on the Algorand blockchain. We want each token to have a configurable behavior and a configurable utility. Additionally, we want all of this data to be transparent and to live on the blockchain. 

![configurations](https://github.com/Vilijan/Tokility/blob/master/images/3.png?raw=true)

The behavior configuration defines how the token will be transferred on the blockchain, while the utility configuration defines what utility the token has in the physical or the virtual world. The blockchain can not verify the properties in the utility configuration, the users need to trust the utility provider that they will provide the utilities that they said would. We do not have any restrictions upon creating the utility configuration.

The stateful smart contract makes sure that for every token interaction, the conditions defined in its behavior configuration are satisfied. This enables the utility providers to define various kinds of behaviors for their tokens. Currently every utility provider needs to provide the following behavior configuration:

- `asa_creator` - contains the address that created the utility token. Usually every utility provider will have their own address. This address will receive the fees from the second-hand economy.
- `asa_price` - defines the price that the users pay when they initially buy the token from the `asa_creator`. 
- `resell_fee` - defines how much the utility provider earns on every successful transaction on the second-hand economy.
- `maxium_sell_price` - the maximum sell price that the utility token can achieve on the second-hand economy.
- `platform_fee` - defines how much our platform receives on every successful transaction on the second-hand economy.
- `reselling_allowed` - boolean value that indicates whether the token can be sold on the second-hand economy.
- `resell_duration` - defines for how long the reselling period will last.
- `gifting_allowed` - boolean value that indicates whether one user can gift the token to another user.

The overall configuration for the token can be represented as a JSON file. Then we can store this configuration on the IPFS peer-to-peer storage network. This means that the configuration is stored on a decentralized database.

```json
{
  "behavior_configuration": {
    "asa_creator": "4QDLSFBRLD6VEAEV7LXETAN32PZB6GNPZESEOWGUC2BWGU6HNB6SCFT37Y",
    "asa_price": 5000000,
    "resell_fee": 100000,
    "maximum_sell_price": 100000000,
    "platform_fee": 10000,
    "reselling_allowed": 1,
    "resell_duration": 1668143794,
    "gifting_allowed": 1
  },

  "utility_configuration": {
    "property_1": "",
    "property_2": "",
    ...
  }
}
```

We can have huge number of tokens issued on the platform, where each token has its own behavior configuration. The stateful smart contract should be able to access those configurations in order to verify and approve transactions. We provide a solution to the following problem:

>  *"How a stateful smart contract will be able to have access to N configurations on the blockchain, where N can get up to millions?"* 

In order to achieve this, we are using a trick with the `Metadata Hash` property for every created Algorand Standard Asset. When issuing an utility token as Algorand Standard Asset we fill the following properties:

- `url` - points to a JSON file on the IPFS storage network. This JSON is similar to the one shown above, and it defines the behavior and the utility for that token. Once the token is issued, its behavior and utility can not be modified.
- `metadata_hash`- this property holds the bytes obtained when the properties in the behavior configuration are concatenated and passed to a `sha256` hash function. This uniquely identifies each behavior configuration, and stores it directly on the blockchain. Later on we will see, how we access this information from the stateful smart contract in order to verify that we are following the right configuration for each token. In the following [code snipet](https://github.com/Vilijan/Tokility/blob/4bcf59a399986039506c001dc9258e0641de09c1/src/models/asset_configurations.py#L109) you can see how the `metadata_hash` is obtained before passing it to a `sha256` hash function.
- `clawback_address` - points to the address of the stateless smart contract. We can transfer the utility token from one address to another only through this stateless smart contract. In there we are making sure that we are always calling the stateful smart contract. 
- `default_frozen` - every utility token is frozen. We want them to be transferred only through the decentralized exchange implemented by the stateful smart contract. Otherwise, we could not be able to limit its behavior on the second-hand economy.

The whole process of creating the NFTs can be summarized in the image below.

![nft deployment](https://github.com/Vilijan/Tokility/blob/master/images/4.png?raw=true)

# Stateful smart contract as a decentralized exchange

Once we have followed the process described above to mint the utility tokens, we can buy and sell them through the stateful smart contract. In order to follow the right behavior configuration for each token, we need to reserve the first nine arguments passed on each application call transaction. The first argument is the method name, while the other eight are the possible behavior configuration properties. Additionally, we always need to pass the `ID` of the token of interest in the `foreign_assets` field.

On every application call transaction, at the beginning we are executing the code below. With this we are making sure that we are following the right behavior configuration for the token of interest. Recall that the `metadata_hash` property of an utility token is set to the `sha256` hash value of the behavior configuration for the token. This operation is performed when we are initially minting the token, and we can not change it afterwards. If the `sha256` hash value of the behavior configuration arguments passed to the smart contract is equal to the `metadata_hash` value of the utility token it means that we are following the right behavior configuration for that token defined at the beginning by the utility provider. In every other case we should reject the transaction, because we are not following the rules that were defined by the utility provider.
With this trick, we can *'store'* as much behavior configurations on the blockchain as we want.

```python
metadata_hash = AssetParam.metadataHash(asset=Txn.assets[0])
concat_args = Concat(Txn.application_args[1],
                     Bytes('-'),
                     Txn.application_args[2],
                     Bytes('-'),
                     Txn.application_args[3],
                     Bytes('-'),
                     Txn.application_args[4],
                     Bytes('-'),
                     Txn.application_args[5],
                     Bytes('-'),
                     Txn.application_args[6],
                     Bytes('-'),
                     Txn.application_args[7],
                     Bytes('-'),
                     Txn.application_args[8])

 return Seq([
            metadata_hash,
            Assert(metadata_hash.hasValue()),
            Assert(metadata_hash.value() == Sha256(concat_args)),
     	    ....])
```

All of the method supported by the tokility decentralized exchange are defined in the `TokilityDEXInterface`.

```python
class TokilityDEXInterface(ABC):

    @abstractmethod
    def initial_buy(self):
        pass

    @abstractmethod
    def sell_asa(self):
        pass

    @abstractmethod
    def buy_from_seller(self):
        pass

    @abstractmethod
    def stop_selling(self):
        pass

    @abstractmethod
    def gift_asa(self):
        pass
```

- `initial_buy` - buy the utility token directly from the utility provider. This is an atomic transfer of three transactions:

  1. Application call to the stateful smart contract where we specify which method we want to get executed.

  2. Payment of `asa_price` from the `buyer_address` to the `asa_creator`. *Note that the `asa_price` and the `buyer_address` are stored in the behavior configuration for that particular token.*

  3. Asset transfer from the `clawback_address` to the `buyer_address`.

- `sell_asa` - a utility token owner issues a sell offer on the second-hand economy for the token that he owns. With this method, for every user of the decentralized exchange we are storing a `key-value` pair in its local state of the application. The `key` represents the `ID` of the token that he is selling, while the `value` represents the price for which he is willing to sell the token. This method is invoked only through a single application call transaction. If we want to see all of the available offers on the decentralized exchange, we query all the accounts that have opted-in to the application and list their local states. 

- `buy_from_seller` - buy the utility token on the second-hand economy. Here we are handling all of the fees applied to the transactions on the second-hand economy. This is an atomic transfer of five transactions:

  1. Application call to the stateful smart contract where we specify which method we want to get executed.
  2. Payment of `resell_fee` from the `buyer_address` to the `asa_creator` address. Here we handle the fees for the utility provider.
  3. Payment from the `buyer_address` to the `seller_address`. The amount of this payment should equal to the amount that the seller set when he offered the utility token through the `sell_asa` method.
  4. Payment of `platform_fee` from the `buyer_address` to the `platform_address`. Here we handle the fees for the platform. 
  5. Asset transfer from the `clawback_address` to the `buyer_address`.

- `stop_selling` - stops a current active sell offer. Only the token owner can stop a sell offer. This method is invoked only through a single application call transaction.

- `gift_asa` - send the utility token that you own to a some address without listing it on the second-hand economy. This is an atomic transfer of four transactions:
  1. Application call to the stateful smart contract where we specify which method we want to get executed.
  2. Payment of `resell_fee` from the `asa_owner_address` to the `asa_creator` address. Here we handle the fees for the utility provider.
  3. Payment of `platform_fee` from the `asa_owner_address` to the `platform_address`. Here we handle the fees for the platform. 
  4. Asset transfer from the `clawback_address` to the `target_address`.

![application call transaction](https://github.com/Vilijan/Tokility/blob/master/images/7.png?raw=true)
