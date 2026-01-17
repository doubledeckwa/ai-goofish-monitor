# Public Marketplace Documentation

## Overview

The Public Marketplace feature allows users to browse products that have been crawled from goofish.com. Users can search, filter, and favorite products without needing to access the admin panel.

## Features

### For Public Users

- **Browse Products**: View all products from public tasks on the main marketplace page
- **Search & Filter**: Search by keywords, filter by price, category, and sort options
- **Product Details**: View detailed product information including images, seller info, and AI recommendations
- **Favorites**: Save products to favorites (requires user registration)
- **User Account**: Register and login to manage favorites

### For Admins

- **Public Task Toggle**: Mark tasks as public to show their products on the marketplace
- **User Management**: View and manage registered users
- **Full Access**: All admin features remain available in the admin panel

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Public Marketplace Configuration
ENABLE_PUBLIC_MARKETPLACE=true

# JWT Configuration for user authentication
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Rate limiting for public API (requests per hour)
PUBLIC_API_RATE_LIMIT=100
```

### Task Publication

1. Go to Admin Panel → Tasks
2. Edit a task or create a new one
3. Enable the "Publish to marketplace" checkbox
4. Save the task

Products from this task will now appear on the public marketplace.

## API Endpoints

### Public API (No Admin Auth Required)

- `GET /api/public/categories` - Get available categories (public tasks)
- `GET /api/public/products` - Search and filter products
- `GET /api/public/products/:id` - Get product details
- `POST /api/public/register` - Register new user
- `POST /api/public/login` - Login user
- `GET /api/public/me` - Get current user (requires auth)
- `GET /api/public/favorites` - Get user's favorites (requires auth)
- `POST /api/public/favorites` - Add to favorites (requires auth)
- `DELETE /api/public/favorites/:product_id` - Remove from favorites (requires auth)
- `POST /api/public/favorites/toggle` - Toggle favorite (requires auth)

### Admin API

- `GET /api/admin/users` - Get all users
- `GET /api/admin/users/:id` - Get user by ID
- `PATCH /api/admin/users/:id` - Update user
- `DELETE /api/admin/users/:id` - Delete user

## Data Filtering

### Public API

The public API filters out sensitive information:
- Seller phone numbers
- Seller email addresses
- Seller QQ/WeChat
- Internal AI analysis data

### Admin API

Admin endpoints return full data including seller contact information.

## Frontend Routes

### Public Routes

- `/` - Main marketplace
- `/products/:id` - Product details
- `/favorites` - User's favorites
- `/user/login` - User login
- `/user/register` - User registration

### Admin Routes

- `/admin/login` - Admin login
- `/admin/tasks` - Task management
- `/admin/accounts` - Account management
- `/admin/results` - View results
- `/admin/logs` - Logs
- `/admin/settings` - Settings

## Security Considerations

1. **JWT Secret**: Always use a strong, random `JWT_SECRET_KEY` in production
2. **Rate Limiting**: Configure appropriate rate limits for the public API
3. **HTTPS**: Use HTTPS in production to protect user credentials
4. **Task Publication**: Only publish tasks with products you want to make publicly accessible
5. **User Data**: All user data is stored in `data/users.json` (consider using a proper database in production)

## File Structure

```
data/
  users.json       - Registered users
  favorites.json   - User favorites

jsonl/
  *.jsonl          - Product data from tasks (existing)
```

## Testing

### Test Public Marketplace

1. Create a task in the admin panel and mark it as public
2. Run the task to populate products
3. Visit the main page (`/`) to see products
4. Test search and filters
5. Register a user and test favorites

### Test Admin Functions

1. Visit `/admin/login`
2. Log in with admin credentials
3. Navigate to Tasks and mark/unmark tasks as public
4. Navigate to Settings to view user management (if implemented)

## Production Deployment

1. Set strong `JWT_SECRET_KEY` in environment
2. Enable HTTPS
3. Configure appropriate rate limits
4. Monitor `data/` directory size (consider database migration)
5. Review and update task publication settings regularly
