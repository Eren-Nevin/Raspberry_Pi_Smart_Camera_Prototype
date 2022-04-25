from flask import Flask, Request, Response, json, request
from flask_socketio import SocketIO, emit, send, leave_room, join_room, \
    disconnect
import db
import json
import http
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
db_name = "listappdev"
users_db_name = "users"

auth_server_check_login_address = "http://127.0.0.1:8833/api/auth/check_login"

connected_users = {}

def authenticate_user_with_auth_server(token=0):
    print("Sending Authentication")
    http_response = requests.post(auth_server_check_login_address,
                                  json={'token': token})
    result = json.loads(http_response.text)
    is_logged_in = result['success']
    if is_logged_in:
        return result['message']
    else:
        return False

    # http.req

def get_current_user(request):
    if request.sid in connected_users:
        return connected_users[request.sid]
    else:
        return None

def get_current_user_item_table(request):
    return db.get_user_item_table(get_current_user(request))

# TODO: Make sure no remove or change is added / queries when there is no
# add item. (You can't remove or change an item that is not added yet).


# TODO: Make a table for each user
try:
    socketio = SocketIO(app, logger=True,
                        # engineio_logger=True,
                        cors_allowed_origins="*",
                        )
    transactions_db_operator = db.TransactionsOperator(db_name)

    # Whenever a connected (thus synced) client pushes a transaction to server
    # it is pushed to all other clients of that user
    @socketio.on('send_transaction_to_server', namespace='/socket.io')
    def handle_message(transaction):
        print(f"Received {transaction}")
        # This is here because for some reason the json sent by react client
        # doesn't get deserialized automatically but the flutter sent one do.
        if (isinstance(transaction, str)):
            transaction = json.loads(transaction)

        transactions_db_operator.add_transaction(transaction,\
                        get_current_user_item_table(request))
        send_transaction_to_client(transaction,
                                   get_current_user(request)['user_id'])
        return True

    @socketio.on('connect', namespace='/socket.io')
    def on_connection(user_auth_data):
        print("Connection Request")
        # print(request.args)
        # Currently the token is passed as url argument (after ?).
        token = request.args['token']
        print(token)
        auth_result = authenticate_user_with_auth_server(token)
        if auth_result:
            # global user
            user = auth_result
            connected_users[request.sid] = user
            # request.user = user
            # print(session)
            print(f"User {user['user_id']} Authenticated")
        else:
            print(f"Authentication Failed, Disconnecting")
            disconnect()
        # if int(token) < 1000:
            # disconnect()
            # socketio.disconnect()
        # print(ap)
        # print(user_auth_data)
        # print(socketio

    @socketio.on('disconnect', namespace='/socket.io')
    def on_disconnect():
        current_user = get_current_user(request)
        if current_user:
            print(
                f"User {current_user['user_id']} Disconnecting")
            del connected_users[request.sid]

    @socketio.on('client_connect_sync', namespace='/socket.io')
    def on_client_connected(user_initial_data_json):
        user_initial_data = json.loads(user_initial_data_json)
        # token = user_initial_data['token']
        # TODO: Use Authentication For User
        # transactions_db_operator.set_user_table_name('items')
        user = get_current_user(request)
        # Currently room name is same as user_id
        join_room(f"{user['user_id']}")
        print(f"A Client Joined Room {user['user_id']}")

        # If any of the transactions are out of order (older than the most recent
        # transaction in the database), it means the client is an out of order
        # client that is just being connected. When this happens all other clients
        # (in same room) should be notified to reset all of their data since the
        # history is change by this out of order client connecting to the server.

        # pending_transactions = json.loads(user_initial_data)
        pending_transactions = user_initial_data
        # pending_transactions = user_initial_data['pending_transactions']
        print(f"Pending Transactions are {pending_transactions}")

        # If the any of the pending requests are older than the most recent
        # transaction available in database right now, then the whole database
        # timeline should be changed for all clients.
        # We first check if for this.
        lastest_transaction_id = \
            transactions_db_operator.get_lastest_transaction_id(\
                            get_current_user_item_table(request))
        isTimelineChanged = len(list(filter(lambda transaction:
                                            transaction['transaction_id'] <
                                            lastest_transaction_id,
                                            pending_transactions))) > 0

        # No matter if the timeline is changed or not, we need to push the
        # pending transactions to the database. We need to do this after
        # checking for timeline changes though.
        transactions_db_operator.add_transactions(\
                pending_transactions, get_current_user_item_table(request))

        if isTimelineChanged:
            print("Timeline Changed")
            # If timeline is changed, all clients (including the connecting
            # client) should reset (reinitialize)
            # their itemlist using the tranaction list that they would receive
            # via the 'send_reset_transactions_to_client' event.
            # Note that the newly connected  client itself doesn't receive the 'send_reset...'
            # event because it gets the transaction list as the return value of
            # its acknowledgement.
            emit('send_reset_transactions_to_client',
                 get_all_transactions_from_db(), to=f"{user['user_id']}",
                 include_self=False)
            pass
        else:
            # If it is not the case (Timeline didn't change), then we safely
            # add all the pending transactions (that are all newer than our newest
            # transaction), to the database and push them to other clients normally
            # like any other transaction using the 'send_transaction_to_client'
            # event.
            # Note that the newly connected client doesn't receive these
            # pending_transactions since it gets a transaction list to
            # reinitialize via its acknowledgement.
            for transaction in pending_transactions:
                send_transaction_to_client(transaction, user['user_id'])

        # This is the initial transaction list for the newly connected client
        return get_all_transactions_from_db()

    # TODO: Make an actual reducer
    def transaction_reducer(transaction_list):
        return transaction_list

    def send_transaction_to_client(transaction, user_id):
        print(f"Sending transaction to {user_id}")
        emit('send_transaction_to_client', transaction,
             to=f"{user_id}", include_self=False)

    def get_all_transactions_from_db():
        return transaction_reducer(transactions_db_operator\
                        .get_transactions_from_database(0,get_current_user_item_table(request)))


# @socketio.on('connect')
# def test_connect(auth):
#     print("Connected")
#     # emit('my response', {'data': 'Connected'})

except Exception:
    transactions_db_operator.close_db()

if __name__ == '__main__':
    socketio.run(app)
