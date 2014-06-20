function numberWithCommas(x) {
    var parts = x.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
}

function update_overall_fiat_total() {
    // Get the totals from each wallet and add them up.
    // Stick that number into the DOM.
    var total = 0;
    $(".fiat-value").each(function(i, element) {
        var number_with_commas = $(element).html();
        total += Number(number_with_commas.replace(",", ''))
    });

    $("#total-fiat-amount").html(total.toLocaleString());
}
function update_DOM_with_price_for_wallet(wallet_id, data) {
    // from a dict of new prices for a wallet, update the DOM
    // gets called after ajax call to get updated price.
    // Updates the wallet, exchange, and fiat value.
    var exchange = data.fiat_exchange;
    if(exchange > 1) {
        exchange = numberWithCommas(exchange.toPrecision(5));
    } else {
        exchange = exchange.toFixed(4);
    }

    var fiat_value = numberWithCommas(data.fiat_value.toFixed(2));
    var wallet_value = numberWithCommas(data.wallet_value);

    $("#" + wallet_id + " .wallet-value").html(wallet_value);
    $("#" + wallet_id + " .fiat-exchange").html(exchange);
    $("#" + wallet_id + " .fiat-value").html(fiat_value);
}

$(function() {
    $("#new-wallet").click(function() {
        $("#new-wallet-modal").bPopup();
    });

    $(".show-transactions").click(function(event) {
        // Get transactions from backend, then plug them into the DOM.
        event.preventDefault()
        var show_transaction = $(this);
        var wallet_id = show_transaction.data("wallet-id");
        var spinner = show_transaction.next();
        var container = spinner.next();
        spinner.show();

        $.ajax({
            url: "/wallet/transactions",
            data: {js_id: wallet_id},
        }).success(function(transactions) {
            console.log(transactions);
            $.each(transactions, function(i, transaction) {
                console.log(transaction);
                var time_utc = transaction['time_utc'];
                var amount = transaction['amount'];
                var txid = transaction['tx'];
                container.html(container.html() + txid + '<br>');
            })
        }).error(function(response) {
            // dump error message to the screen, figure it out later.
            container.html("oh snap!! error!! " + response.responseText);
        }).complete(function() {
            spinner.hide();
        });
    });

    $(".reload-wallet-price").click(function(event) {
        // Get the current price from the backend, and then update the
        // front end with new wallet totals.
        event.preventDefault();
        var wallet_id = $(this).data('wallet-id');
        var wallet = $("#" + wallet_id);
        var spinner = wallet.find(".price-spinner");
        spinner.show();
        $("#overall-spinner").show();

        $.ajax({
            url: "/wallet/value",
            data: {js_id: wallet_id}
        }).success(function(data) {
            // returned will be new totals for this wallet
            // plug into front end.
            update_DOM_with_price_for_wallet(wallet_id, data);
            update_overall_fiat_total();
        }).error(function(response) {
            wallet.find('.error').html("oh snap!! error!! " + response.responseText);
        }).complete(function() {
            spinner.hide();
            $("#overall-spinner").hide();
        });
    });

    $(".launch-public-qr-modal").click(function(event) {
        event.preventDefault();
        var modal = $(this).prev();
        var public_key = $(this).data('public-key');
        modal.find(".modal-contents").qrcode(public_key);
        modal.bPopup();
    });

    $(".launch-private-qr-modal").click(function(event) {
        // Make ajax call to get the private key from the server.
        // This is done to prevent private keys from being accidently stolen.
        event.preventDefault();
        //debugger;
        var modal = $(this).prev();
        var js_id = $(this).data('js-id');

        $.ajax({
            url: "/wallets/get_private_key/",
            data: {js_id: js_id},
        }).success(function(private_key){
            console.log("returned private key");
            modal.find(".modal-contents").qrcode(private_key);
            modal.find(".modal-bottom-section").text(private_key);
            modal.bPopup();
        });

    });

});
