import sqlite3
import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Environment:
    
    def __init__(self, domain: str, domain_path: str):
        self.domain = domain
        self.domain_path = domain_path
        self.db_path = ":memory:"
        self.conn = None
        self.tools = {}
        self.policies = {}
        self.conversation_history = []
        self.initial_state = {}
        self.goal_state = {}
        
        self._load_domain_config()
    
    def validate_setup(self) -> bool:
        """Validate that the environment is properly configured."""
        try:
            # Check database connection
            if not self.conn:
                logger.error("Database connection not established")
                return False
            
            # Check tables exist
            cursor = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = {
                'airline': ['users', 'flights', 'bookings'],
                'retail': ['customers', 'products', 'orders', 'order_items']
            }
            
            domain_tables = required_tables.get(self.domain, [])
            missing_tables = [t for t in domain_tables if t not in tables]
            
            if missing_tables:
                logger.error(f"Missing required tables: {missing_tables}")
                return False
            
            # Check tools loaded
            if not self.tools:
                logger.error("No tools loaded")
                return False
            
            logger.info(f"Environment validation passed for domain: {self.domain}")
            return True
            
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return False
    
    def _load_domain_config(self):
        schema_path = os.path.join(self.domain_path, "schema.sql")
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.executescript(schema_sql)
        
        data_path = os.path.join(self.domain_path, "data.csv")
        self._load_csv_data(data_path)
        
        tools_path = os.path.join(self.domain_path, "tools.py")
        tools_module = self._load_tools_module(tools_path)
        self.tools = tools_module.TOOLS
        
        policy_path = os.path.join(self.domain_path, "policy.txt")
        with open(policy_path, 'r') as f:
            self.policies = f.read()
    
    def _load_csv_data(self, data_path: str):
        with open(data_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split(',')
                table_name = parts[0]
                values = parts[1:]
                
                cursor = self.conn.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                
                placeholders = ','.join(['?' for _ in values])
                query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
                self.conn.execute(query, values)
        
        self.conn.commit()
    
    def _load_tools_module(self, tools_path: str):
        import importlib.util
        spec = importlib.util.spec_from_file_location("tools", tools_path)
        tools_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tools_module)
        return tools_module
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        self.conversation_history.append({
            "type": "tool_call",
            "tool": tool_name,
            "args": kwargs,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            if self.domain == "airline":
                result = self._execute_airline_tool(tool_name, **kwargs)
            elif self.domain == "retail":
                result = self._execute_retail_tool(tool_name, **kwargs)
            else:
                result = {"error": f"Unknown domain: {self.domain}"}
        except Exception as e:
            result = {"error": str(e)}
        
        self.conversation_history.append({
            "type": "tool_result",
            "tool": tool_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    
    def _execute_airline_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        if tool_name == "search_flights":
            return self._search_flights(**kwargs)
        elif tool_name == "book_flight":
            return self._book_flight(**kwargs)
        elif tool_name == "cancel_booking":
            return self._cancel_booking(**kwargs)
        elif tool_name == "check_policy":
            return self._check_policy(**kwargs)
        elif tool_name == "respond_to_user":
            return self._respond_to_user(**kwargs)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def _execute_retail_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        if tool_name == "search_products":
            return self._search_products(**kwargs)
        elif tool_name == "place_order":
            return self._place_order(**kwargs)
        elif tool_name == "return_item":
            return self._return_item(**kwargs)
        elif tool_name == "check_inventory":
            return self._check_inventory(**kwargs)
        elif tool_name == "check_policy":
            return self._check_policy(**kwargs)
        elif tool_name == "respond_to_user":
            return self._respond_to_user(**kwargs)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def _search_flights(self, destination: str, date: str) -> Dict[str, Any]:
        cursor = self.conn.execute(
            "SELECT * FROM flights WHERE destination = ? AND departure_date = ?",
            (destination, date)
        )
        flights = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
        return {"flights": flights}
    
    def _book_flight(self, flight_id: int, user_id: int) -> Dict[str, Any]:
        cursor = self.conn.execute("SELECT * FROM flights WHERE id = ?", (flight_id,))
        flight = cursor.fetchone()
        if not flight:
            return {"error": "Flight not found"}
        
        flight_dict = dict(zip([col[0] for col in cursor.description], flight))
        if flight_dict['available_seats'] <= 0:
            return {"error": "No seats available"}
        
        booking_date = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.execute(
            "INSERT INTO bookings (user_id, flight_id, booking_date, status) VALUES (?, ?, ?, ?)",
            (user_id, flight_id, booking_date, "confirmed")
        )
        booking_id = cursor.lastrowid
        
        self.conn.execute(
            "UPDATE flights SET available_seats = available_seats - 1 WHERE id = ?",
            (flight_id,)
        )
        self.conn.commit()
        
        return {"booking_id": booking_id, "status": "confirmed"}
    
    def _cancel_booking(self, booking_id: int) -> Dict[str, Any]:
        cursor = self.conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        booking = cursor.fetchone()
        if not booking:
            return {"error": "Booking not found"}
        
        booking_dict = dict(zip([col[0] for col in cursor.description], booking))
        booking_date = datetime.strptime(booking_dict['booking_date'], "%Y-%m-%d")
        days_ago = (datetime.now() - booking_date).days
        
        if days_ago > 1:
            return {"error": "Cancellation not allowed after 24 hours"}
        
        self.conn.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE id = ?",
            (booking_id,)
        )
        
        self.conn.execute(
            "UPDATE flights SET available_seats = available_seats + 1 WHERE id = ?",
            (booking_dict['flight_id'],)
        )
        self.conn.commit()
        
        return {"status": "cancelled"}
    
    def _search_products(self, category: str = None, name: str = None) -> Dict[str, Any]:
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        
        cursor = self.conn.execute(query, params)
        products = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
        return {"products": products}
    
    def _place_order(self, customer_id: int, product_ids: List[int], quantities: List[int]) -> Dict[str, Any]:
        if len(product_ids) != len(quantities):
            return {"error": "Product IDs and quantities must match"}
        
        for product_id, quantity in zip(product_ids, quantities):
            cursor = self.conn.execute("SELECT stock_quantity FROM products WHERE id = ?", (product_id,))
            stock = cursor.fetchone()
            if not stock or stock[0] < quantity:
                return {"error": f"Insufficient stock for product {product_id}"}
        
        order_date = datetime.now().strftime("%Y-%m-%d")
        total_amount = 0
        
        for product_id, quantity in zip(product_ids, quantities):
            cursor = self.conn.execute("SELECT price FROM products WHERE id = ?", (product_id,))
            price = cursor.fetchone()[0]
            total_amount += price * quantity
        
        cursor = self.conn.execute(
            "INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES (?, ?, ?, ?)",
            (customer_id, order_date, total_amount, "completed")
        )
        order_id = cursor.lastrowid
        
        for product_id, quantity in zip(product_ids, quantities):
            cursor = self.conn.execute("SELECT price FROM products WHERE id = ?", (product_id,))
            unit_price = cursor.fetchone()[0]
            
            self.conn.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (order_id, product_id, quantity, unit_price)
            )
            
            self.conn.execute(
                "UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                (quantity, product_id)
            )
        
        self.conn.commit()
        return {"order_id": order_id, "status": "completed", "total_amount": total_amount}
    
    def _return_item(self, order_id: int, item_id: int, reason: str) -> Dict[str, Any]:
        cursor = self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            return {"error": "Order not found"}
        
        order_dict = dict(zip([col[0] for col in cursor.description], order))
        order_date = datetime.strptime(order_dict['order_date'], "%Y-%m-%d")
        days_ago = (datetime.now() - order_date).days
        
        if days_ago > 30:
            return {"error": "Return window expired (30 days)"}
        
        self.conn.execute(
            "UPDATE order_items SET quantity = quantity - 1 WHERE id = ?",
            (item_id,)
        )
        
        cursor = self.conn.execute("SELECT product_id FROM order_items WHERE id = ?", (item_id,))
        product_id = cursor.fetchone()[0]
        self.conn.execute(
            "UPDATE products SET stock_quantity = stock_quantity + 1 WHERE id = ?",
            (product_id,)
        )
        
        self.conn.commit()
        return {"status": "returned", "reason": reason}
    
    def _check_inventory(self, product_id: int) -> Dict[str, Any]:
        cursor = self.conn.execute("SELECT stock_quantity FROM products WHERE id = ?", (product_id,))
        stock = cursor.fetchone()
        if not stock:
            return {"error": "Product not found"}
        
        return {"stock_quantity": stock[0]}
    
    def _check_policy(self, policy_type: str) -> Dict[str, Any]:
        if policy_type == "cancellation":
            return {"policy": "Cancellations within 24 hours get full refund"}
        elif policy_type == "return_window":
            return {"policy": "Returns accepted within 30 days"}
        elif policy_type == "loyalty_discount":
            return {"policy": "10% discount for 100+ loyalty points"}
        else:
            return {"error": "Unknown policy type"}
    
    def _respond_to_user(self, message: str) -> Dict[str, Any]:
        return {"message": message, "status": "sent"}
    
    def get_current_state(self) -> Dict[str, Any]:
        state = {}
        
        cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            cursor = self.conn.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            state[table] = [dict(zip(columns, row)) for row in rows]
        
        return state
    
    def evaluate_success(self, goal_state: Dict[str, Any]) -> bool:
        current_state = self.get_current_state()
        
        for table, expected_rows in goal_state.items():
            if table not in current_state:
                return False
            
            current_rows = current_state[table]
            
            for expected_row in expected_rows:
                found = False
                for current_row in current_rows:
                    if all(current_row.get(k) == v for k, v in expected_row.items()):
                        found = True
                        break
                
                if not found:
                    return False
        
        return True
    
    def reset_to_state(self, initial_state: Dict[str, Any]):
        """Reset the environment to a specific initial state."""
        try:
            # Clear existing data
            cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                self.conn.execute(f"DELETE FROM {table}")
            
            # Insert new data
            for table, rows in initial_state.items():
                if not rows:
                    continue
                    
                if table not in tables:
                    logger.warning(f"Table {table} not found in database, skipping")
                    continue
                
                # Get columns from the first row
                columns = list(rows[0].keys())
                placeholders = ','.join(['?' for _ in columns])
                query = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                
                for row in rows:
                    values = [row[col] for col in columns]
                    self.conn.execute(query, values)
            
            self.conn.commit()
            logger.info("Environment reset to initial state")
            
        except Exception as e:
            logger.error(f"Failed to reset environment: {e}")
            raise

    def close(self):
        if self.conn:
            self.conn.close()
