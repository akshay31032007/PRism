import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

export default withAuth(
  function middleware(req) {
    // User is authenticated — let them through
    return NextResponse.next();
  },
  {
    callbacks: {
      // authorized() decides who can access the matched routes
      // returning false redirects to the signIn page
      authorized: ({ token }) => !!token,
    },
  }
);

// Protect these routes — any unauthenticated visit redirects to /signin
export const config = {
  matcher: ["/repos/:path*", "/history/:path*"],
};
