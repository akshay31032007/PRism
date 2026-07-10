import "next-auth";
import "next-auth/jwt";

// Extend the built-in session/JWT types to include accessToken
declare module "next-auth" {
  interface Session {
    accessToken?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    provider?:    string;
  }
}
