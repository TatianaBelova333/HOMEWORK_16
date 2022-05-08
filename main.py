from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import utils


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['JSON_AS_ASCII'] = False
app.config["JSON_SORT_KEYS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.Text(), nullable=False)
    last_name = db.Column(db.Text(), nullable=False)
    age = db.Column(db.Integer, db.CheckConstraint('age > 15'))
    email = db.Column(db.Text(), nullable=False)
    role = db.Column(db.Text(), nullable=False)
    phone = db.Column(db.Text(), nullable=False)
    offers = db.relationship('Offer', cascade="all, delete")


class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text(), nullable=False)
    description = db.Column(db.Text(), nullable=False)
    start_date = db.Column(db.String)
    end_date = db.Column(db.String)
    address = db.Column(db.Text(), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    executor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    offers = db.relationship('Offer')
    customer = db.relationship('User', foreign_keys=[customer_id])
    executor = db.relationship('User', foreign_keys=[executor_id])


class Offer(db.Model):
    __tablename__ = 'offer'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    executor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    order = db.relationship('Order')
    executor = db.relationship('User')


@app.route('/users', methods=['GET', 'POST'])
def users_index():
    if request.method == 'GET':
        all_users = db.session.query(User).all()
        result = []
        for user in all_users:
            result.append(utils.user_instance_to_dict(user))
        return jsonify(result)
    elif request.method == 'POST':
        data = request.get_json()
        new_user = User(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            age=data.get('age'),
            email=data.get('email'),
            role=data.get('role'),
            phone=data.get('phone'),
        )
        with db.session.begin():
            db.session.add(new_user)
        return jsonify(utils.user_instance_to_dict(new_user))


@app.route('/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
def get_update_delete_user_by_id(user_id):
    if request.method == 'GET':
        one_user = db.session.query(User).get_or_404(
            user_id,
            description='There is no user with id {}'.format(user_id)
        )
        result = utils.user_instance_to_dict(one_user)
        return jsonify(result)
    elif request.method == 'PUT':
        request_data = request.json
        user_to_update = db.session.query(User).get_or_404(
            user_id,
            description='There is no user with id {}'.format(user_id)
        )
        if request_data:
            if 'first_name' in request_data:
                user_to_update.first_name = request_data['first_name']
            if 'last_name' in request_data:
                user_to_update.last_name = request_data['last_name']
            if 'age' in request_data:
                user_to_update.age = request_data['age']
            if 'email' in request_data:
                user_to_update.email = request_data['email']
            if 'role' in request_data:
                user_to_update.role = request_data['role']
            if 'phone' in request_data:
                user_to_update.phone = request_data['phone']
        db.session.add(user_to_update)
        db.session.commit()
        return jsonify(utils.user_instance_to_dict(user_to_update))
    elif request.method == 'DELETE':
        user = User.query.get_or_404(
            user_id,
            description='There is no user with id {}'.format(user_id)
        )
        db.session.delete(user)
        db.session.commit()
        return jsonify(f'User with id {user_id} has been deleted')


@app.route('/orders', methods=['GET', 'POST'])
def get_all_orders():
    if request.method == 'GET':
        customer = db.aliased(User)
        executor = db.aliased(User)
        all_orders = db.session.query(
            Order.id,
            Order.description.label('order_description'),
            (Order.start_date + ' - ' + Order.end_date).label('date_frame'),
            Order.address,
            Order.price,
            (customer.first_name + ' ' + customer.last_name).label('customer_full_name'),
            (executor.first_name + ' ' + executor.last_name).label('executor_full_name')
        ).join(customer, Order.customer_id == customer.id).join(executor, executor.id == Order.executor_id).all()
        result = []
        for order in all_orders:
            one_order = order._asdict()
            result.append(one_order)
        return jsonify(result)
    elif request.method == 'POST':
        data = request.get_json()
        new_order = Order(
            name=data.get('name'),
            description=data.get('description'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            address=data.get('address'),
            price=data.get('price'),
            customer_id=data.get('customer_id'),
            executor_id=data.get('executor_id')
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify(utils.order_instance_to_dict(new_order))


@app.route('/orders/<int:order_id>', methods=['GET', 'PUT', 'DELETE'])
def get_order_by_id(order_id):
    if request.method == 'GET':
        customer = db.aliased(User)
        executor = db.aliased(User)
        order = db.session.query(
            Order.id,
            Order.description.label('order_description'),
            (Order.start_date + ' - ' + Order.end_date).label('date_frame'),
            Order.address,
            Order.price,
            (customer.first_name + ' ' + customer.last_name).label('customer_full_name'),
            (executor.first_name + ' ' + executor.last_name).label('executor_full_name')
        ).join(customer, Order.customer_id == customer.id). \
            join(executor, executor.id == Order.executor_id). \
            filter(Order.id == order_id).first_or_404(
            description='There is no order with id {}'.format(order_id)
        )
        return jsonify(order._asdict())
    elif request.method == 'DELETE':
        order_to_delete = Order.query.get_or_404(
            order_id,
            description='There is no order with id {}'.format(order_id)
        )
        db.session.delete(order_to_delete),
        db.session.commit()
        return jsonify(f'Order with id {order_id} has been deleted')
    elif request.method == 'PUT':
        order_to_update = Order.query.get_or_404(
            order_id,
            description='There is no order with id {}'.format(order_id)
        )
        data = request.get_json()
        if data:
            if 'name' in data:
                order_to_update.name = data['name']
            if 'description' in data:
                order_to_update.description = data['description']
            if 'start_date' in data:
                order_to_update.start_date = data['start_date']
            if 'end_date' in data:
                order_to_update.end_date = data['end_date']
            if 'address' in data:
                order_to_update.address = data['address']
            if 'price' in data:
                order_to_update.price = data['price']
            if 'customer_id' in data:
                order_to_update.customer_id = data['customer_id']
            if 'executor_id' in data:
                order_to_update.executor_id = data['executor_id']
            db.session.add(order_to_update)
            db.session.commit()
            return jsonify(utils.order_instance_to_dict(order_to_update))


@app.route('/offers', methods=['GET', 'POST'])
def offers_index():
    if request.method == 'GET':
        all_offers = db.session.query(
            Offer.id,
            Offer.order_id,
            Order.description,
            Order.start_date + ' - ' + Order.end_date,
            User.first_name + ' ' + User.last_name,
        ).join(Offer.order).join(Offer.executor).all()
        result = []
        for offer in all_offers:
            one_offer = {
                "offer_id": offer[0],
                "order_id": offer[1],
                "order_description": offer[2],
                "time_frame": offer[3],
                "executor_name": offer[4]
            }
            result.append(one_offer)
        return jsonify(result)
    elif request.method == 'POST':
        request_data = request.json
        new_offer = Offer(
            order_id=request_data.get('order_id'),
            executor_id=request_data.get('executor_id')
        )
        with db.session.begin():
            db.session.add(new_offer)
        result = {
            "id": new_offer.id,
            "order_id": new_offer.order_id,
            "executor_id": new_offer.executor_id
        }
        return jsonify(result)


@app.route('/offers/<int:offer_id>', methods=['GET', 'PUT', 'DELETE'])
def get_update_delete_offer_by_id(offer_id):
    if request.method == 'GET':
        offer = db.session.query(
            Offer.id,
            Offer.order_id,
            Order.name.label('order_title'),
            (Order.start_date + ' - ' + Order.end_date).label('date_frame'),
            (User.first_name + " " + User.last_name).label('executor_full_name'),
            User.age,
            (User.email + ', ' + User.phone).label('contact_information'),
        ).join(Offer.order).join(Offer.executor).filter(Offer.id == offer_id).first_or_404(
            description='There is no offer with id {}'.format(offer_id)
        )
        return jsonify(offer._asdict())
    elif request.method == 'PUT':
        request_data = request.json
        offer_to_update = db.session.query(Offer).get_or_404(
            offer_id,
            description='There is no offer with id {}'.format(offer_id))
        if "order_id" in request_data:
            offer_to_update.order_id = request_data["order_id"]
        if "executor_id" in request_data:
            offer_to_update.executor_id = request_data["executor_id"]
        db.session.add(offer_to_update )
        db.session.commit()
        return f'Offer with id {offer_id} has been updated'
    elif request.method == 'DELETE':
        offer_to_delete = Offer.query.get_or_404(
            offer_id,
            description='There is no offer with id {}'.format(offer_id)
        )
        db.session.delete(offer_to_delete)
        db.session.commit()
        return jsonify(f'Offer with id {offer_id} has been deleted')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
