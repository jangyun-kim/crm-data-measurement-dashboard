import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(req: Request) {
  const body = await req.json();
  const customerId = body?.customerId as string;
  const payload = body?.payload;

  if (!customerId || !payload) {
    return NextResponse.json(
      { error: "customerId/payload required" },
      { status: 400 }
    );
  }

  const consult = await prisma.consult.create({
    data: { customerId, payload },
  });

  return NextResponse.json({ consult });
}
