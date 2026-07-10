import NextAuth from "next-auth";
import GitHubProvider from "next-auth/providers/github";
import type { NextAuthOptions } from "next-auth";

const authOptions: NextAuthOptions = {
  providers: [
    GitHubProvider({
      clientId:     process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
      authorization: {
        params: { scope: "read:user user:email repo" },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.provider    = account.provider;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string | undefined;
      return session;
    },
  },
  pages: {
    signIn:  "/signin",
    signOut: "/signin",
    error:   "/signin",
  },
  session: {
    strategy: "jwt",
    maxAge:   30 * 24 * 60 * 60,
  },
  secret: process.env.NEXTAUTH_SECRET,
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handler: any = NextAuth(authOptions);
export { handler as GET, handler as POST };
