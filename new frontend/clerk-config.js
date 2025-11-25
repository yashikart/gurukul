// Clerk configuration to skip phone verification
export const clerkConfig = {
  signUp: {
    // Disable phone number requirement entirely
    phoneNumber: {
      enabled: false,
      required: false
    },
    // Use email + password authentication
    emailAddress: {
      required: true
    },
    password: {
      required: true
    }
  },
  signIn: {
    strategy: "password" // Use password-based sign in
  },
  // Disable phone number globally
  phoneNumber: {
    enabled: false
  }
};