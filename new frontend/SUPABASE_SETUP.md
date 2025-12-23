# Supabase Setup for Gurukul Platform

This document outlines the setup process for the new Supabase project used for authentication and data storage in the Gurukul platform.

## Project Details

- **Project URL**: https://aczmbrhfzankcvpbjavt.supabase.co
- **Anonymous Key**: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjem1icmhmemFua2N2cGJqYXZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1Njg1MDIsImV4cCI6MjA4MDE0NDUwMn0.PsCxt3xyBGlh6BskcqDH5ojPLDjWRLMwgNYW-8eKBys

## Setup Instructions

### 1. Database Tables

The following tables need to be created in your Supabase project:

1. `user_goals` - Stores daily study goals for each user
2. `user_settings` - Stores user preferences and settings

Run the SQL migration script located at `supabase/migrations/001_initial_tables.sql` to create these tables.

### 2. Authentication Configuration

The platform uses Supabase Auth for user management with the following configuration:

- Email/Password authentication enabled
- OAuth providers (Google) enabled
- Email confirmation required for new signups
- Password reset functionality enabled

### 3. Environment Variables

The following environment variables are configured in the `.env` file:

```env
VITE_SUPABASE_URL=https://aczmbrhfzankcvpbjavt.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjem1icmhmemFua2N2cGJqYXZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1Njg1MDIsImV4cCI6MjA4MDE0NDUwMn0.PsCxt3xyBGlh6BskcqDH5ojPLDjWRLMwgNYW-8eKBys
```

## Testing the Setup

1. Start the development server:
   ```bash
   npm run dev
   ```

2. Navigate to http://localhost:5173

3. Try signing up with a new email address

4. Check your email for the verification link

5. After verifying, you should be able to sign in and access the dashboard

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Make sure the Supabase URL and anon key are correctly set in the `.env` file.

2. **Database Connection Error**: Verify that the Supabase project is active and the credentials are correct.

3. **Email Not Received**: Check spam/junk folders. For development, you can also check the Supabase Auth logs in the dashboard.

### Need Help?

If you encounter any issues with the Supabase setup, check the Supabase documentation or contact support at https://supabase.com/support.