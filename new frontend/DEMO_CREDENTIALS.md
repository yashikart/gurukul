# Demo Login Credentials

## Test Account for Clerk Authentication

### Demo User 1
- **Email**: demo@gurukul.com
- **Password**: Demo@123456

### Demo User 2
- **Email**: test@gurukul.com
- **Password**: Test@123456

## Demo Mode Access

If Clerk authentication is not working (development instance limits), you can use **Demo Mode**:

1. Click "Continue in Demo Mode" button on the Sign In page
2. This bypasses authentication for development/testing purposes
3. All features will be accessible without authentication

## Clerk Configuration

Current Clerk Publishable Key: `pk_test_aGlwLWdhdG9yLTMxLmNsZXJrLmFjY291bnRzLmRldiQ`

### To create test users in Clerk Dashboard:
1. Go to https://dashboard.clerk.com
2. Navigate to your application
3. Go to "Users" section
4. Click "Create User"
5. Add the demo credentials above

## Backend API Endpoints

- Base Backend: http://localhost:8000
- Chat API: http://localhost:8001
- Financial API: http://localhost:8002
- Memory API: http://localhost:8003
- Agent API: http://localhost:8005

## Testing Authentication Flow

1. **Sign Up Flow**:
   - Go to `/signup`
   - Enter email and password
   - Verify email with code sent to inbox
   - Redirect to sign in

2. **Sign In Flow**:
   - Go to `/signin`
   - Enter credentials
   - Successful login redirects to `/home`

3. **OAuth Flow**:
   - Click "Sign in with Google"
   - Complete OAuth flow
   - Redirect to `/home`

4. **Demo Mode**:
   - Click "Continue in Demo Mode"
   - Instant access without authentication
   - Stored in localStorage

## Troubleshooting

### 422 Error (Development Instance Limit)
- Clerk free tier has user limits
- Use Demo Mode for testing
- Or upgrade Clerk plan

### Missing Publishable Key
- Check `.env` file has `VITE_CLERK_PUBLISHABLE_KEY`
- Restart dev server after adding

### CORS Issues
- Backend must allow frontend origin
- Check `ALLOWED_ORIGINS` in backend `.env`
