import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(
  _req: Request,
  { params }: { params: { id: string } }
) {
  const customerId = params.id;

  const consults = await prisma.consult.findMany({
    where: { customerId },
    orderBy: { createdAt: "desc" },
    take: 50,
  });

  return NextResponse.json({ consults });
}
