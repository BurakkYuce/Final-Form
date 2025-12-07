module isim::stake {
    use sui::coin::{Self, Coin};
    use sui::sui::SUI;
    use sui::balance::{Self, Balance};
    use sui::table::{Self, Table};
    use sui::event;

    // Hata kodları
    const EZeroAmount: u64 = 0;
    const EInsufficientStake: u64 = 1;
    const ENoStakeFound: u64 = 2;

    public struct StakePool has key, store {
        id: UID,
        // Kullanıcıların yatırdığı SUI'leri tutan kasa
        balance: Balance<SUI>,
        // Kimin ne kadar yatırdığını tutan defter (Adres -> Miktar)
        stakes: Table<address, u64>
    }

    // Eventler (Frontend dinleyebilir)
    public struct Staked has copy, drop { user: address, amount: u64 }
    public struct Unstaked has copy, drop { user: address, amount: u64 }

    fun init(ctx: &mut TxContext) {
        let pool = StakePool {
            id: object::new(ctx),
            balance: balance::zero(),
            stakes: table::new(ctx),
        };
        transfer::share_object(pool);
    }

    // --- STAKE ---
    // Kullanıcı Coin<SUI> gönderir.
    public fun stake(
        pool: &mut StakePool,
        payment: Coin<SUI>,
        ctx: &mut TxContext
    ) {
        let amount = coin::value(&payment);
        assert!(amount > 0, EZeroAmount);

        let sender = ctx.sender();

        // 1. Coin'i Balance'a çevirip kasaya koy
        let coin_balance = coin::into_balance(payment);
        balance::join(&mut pool.balance, coin_balance);

        // 2. Tabloyu güncelle
        if (table::contains(&pool.stakes, sender)) {
            let current_stake = table::borrow_mut(&mut pool.stakes, sender);
            *current_stake = *current_stake + amount;
        } else {
            table::add(&mut pool.stakes, sender, amount);
        };

        event::emit(Staked { user: sender, amount });
    }

    // --- UNSTAKE ---
    public fun unstake(
        pool: &mut StakePool,
        amount: u64,
        ctx: &mut TxContext
    ) {
        let sender = ctx.sender();
        assert!(table::contains(&pool.stakes, sender), ENoStakeFound);

        let user_stake = table::borrow_mut(&mut pool.stakes, sender);
        assert!(*user_stake >= amount, EInsufficientStake);

        // 1. Tablodan düş
        *user_stake = *user_stake - amount;

        // Eğer 0 kaldıysa tablodan silebiliriz (isteğe bağlı, gas iadesi için iyi olur)
        if (*user_stake == 0) {
            table::remove(&mut pool.stakes, sender);
        };

        // 2. Kasadan para çıkar ve kullanıcıya yolla
        let withdrawn = balance::split(&mut pool.balance, amount);
        let coin = coin::from_balance(withdrawn, ctx);
        
        transfer::public_transfer(coin, sender);

        event::emit(Unstaked { user: sender, amount });
    }

    // --- VIEW ---
    public fun get_user_stake(pool: &StakePool, user: address): u64 {
        if (!table::contains(&pool.stakes, user)) {
            return 0
        };
        *table::borrow(&pool.stakes, user)
    }
}