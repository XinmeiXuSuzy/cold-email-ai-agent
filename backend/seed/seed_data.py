"""
Seed the database with sample prospects and memory items for development.
Run with: python -m seed.seed_data
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
from app.database import Base
from app.models.prospect import Prospect
from app.models.memory import MemoryItem

PROSPECTS = [
    {
        "name": "Sarah Chen",
        "email": "sarah.chen@vertextech.io",
        "role": "VP of Engineering",
        "company": "Vertex Technologies",
        "industry": "SaaS",
        "website": "https://vertextech.io",
        "linkedin_url": "https://linkedin.com/in/sarahchen",
        "notes": "Grew team from 8 to 35 engineers in 2 years. Focused on dev tooling and platform reliability.",
        "outreach_status": "new",
    },
    {
        "name": "Marcus Rivera",
        "email": "marcus@growthloop.com",
        "role": "Head of Growth",
        "company": "GrowthLoop",
        "industry": "MarTech",
        "website": "https://growthloop.com",
        "notes": "Former Stripe PM. Led growth at two YC companies. Obsessed with data-driven activation.",
        "outreach_status": "researched",
    },
    {
        "name": "Priya Nair",
        "email": "priya.nair@cloudspire.ai",
        "role": "CTO",
        "company": "CloudSpire AI",
        "industry": "AI Infrastructure",
        "website": "https://cloudspire.ai",
        "notes": "Ex-Google Brain. Building MLOps toolchain for mid-market. Raised Series A last quarter.",
        "outreach_status": "new",
    },
    {
        "name": "James Whitfield",
        "email": "j.whitfield@meridianops.com",
        "role": "Director of Operations",
        "company": "Meridian Ops",
        "industry": "Logistics",
        "website": "https://meridianops.com",
        "notes": "Oversees 200+ ops staff. Pain point: manual workflow coordination across warehouses.",
        "outreach_status": "new",
    },
    {
        "name": "Ananya Bose",
        "email": "ananya@finstack.co",
        "role": "Co-founder & CEO",
        "company": "FinStack",
        "industry": "FinTech",
        "website": "https://finstack.co",
        "linkedin_url": "https://linkedin.com/in/ananyabose",
        "notes": "Building embedded finance APIs for SMBs. Previously at Plaid. Looking for go-to-market partnerships.",
        "outreach_status": "sent",
    },
]

MEMORY_ITEMS = [
    {
        "memory_type": "note",
        "content": "SaaS VP of Engineering personas respond well to messaging around developer productivity and reducing oncall burden. Avoid generic ROI framing.",
    },
    {
        "memory_type": "note",
        "content": "MarTech leads care about attribution accuracy and CAC reduction. Reference specific metrics like 'improved MQL-to-SQL by X%' when possible.",
    },
    {
        "memory_type": "note",
        "content": "AI/ML infrastructure buyers are skeptical of hype. Lead with technical credibility and show that you understand their stack.",
    },
    {
        "memory_type": "note",
        "content": "FinTech founders appreciate blunt outreach. No fluff. Get to the value prop in sentence two.",
    },
]


async def seed():
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        # Check if already seeded
        from sqlalchemy import select
        result = await session.execute(select(Prospect).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        for p_data in PROSPECTS:
            prospect = Prospect(**p_data)
            session.add(prospect)

        for m_data in MEMORY_ITEMS:
            memory = MemoryItem(**m_data, embedding=None)
            session.add(memory)

        await session.commit()
        print(f"Seeded {len(PROSPECTS)} prospects and {len(MEMORY_ITEMS)} memory items.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
