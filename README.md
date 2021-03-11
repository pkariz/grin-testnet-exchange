# Grin testnet exchange
Example of how exchanges can integrate grin.

# Run locally
1.  fill out the missing ENV variables in `.env` (you can also set wallet address of the exchange in `.env.development`, although that's only used to display it to the user)
2.  run grin-node on localhost standard port
3.  rin grin-wallet owner_api on standard port
4.  Install `nix` package manager.
5.  run `nix-shell` in project root
6.  run `yarn install` in project root inside of nix-shell
7.  run `docker-compose up` and go to `localhost:8080`
