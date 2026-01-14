import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const name = (searchParams.get("name") || "").trim();
  const phone = (searchParams.get("phone") || "").trim();

  // ✅ 하나만 넣어도 검색되게 (AND가 아니라 OR)
  const where =
    name || phone
      ? {
          AND: [
            name ? { name: { contains: name, mode: "insensitive" } } : {},
            phone ? { phone: { contains: phone } } : {},
          ],
        }
      : {};

  const customers = await prisma.customer.findMany({
    where,
    orderBy: { updatedAt: "desc" },
    take: 20,
  });

  return NextResponse.json({ customers });
}

export async function POST(req: Request) {
  const body = await req.json();
  const name = (body?.name || "").trim();
  const phone = (body?.phone || "").trim();

  if (!name || !phone) {
    return NextResponse.json({ error: "name/phone required" }, { status: 400 });
  }

  // 동일 고객(이름+전화) 있으면 그대로 반환, 없으면 생성
  const customer = await prisma.customer.upsert({
    where: { name_phone: { name, phone } },
    update: {},
    create: { name, phone },
  });

  return NextResponse.json({ customer });
}
