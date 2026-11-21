# Online-Shop
It is an online shop stimulator.
Users can register and log in.
Anyone can list products.
Logged-in users can view an order by ID and search their orders.
There are admin routes: list all users, and a "diagnose" page that pings a host.
There are integrations: a shipping-rate lookup that calls a carrier URL, a config import, and a backup restore.
The database is on Supabase, with tables for profiles, orders, notes and payments.
The frontend is a pre-built JavaScript bundle that loads orders and checks out.
