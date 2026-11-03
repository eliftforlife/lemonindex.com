# Vote page polls (11-03, Elijah: "a vote page on Lemon and Business for people to vote on brands, models, years, insurance companies...
# with a selector: lifetime, weekly, monthly, 6 months"). Writes data/votes.json, the single list for BOTH sites:
#   lemon -> lemonindex.com/vote/ (ids vl_*), bs -> thebusinessstudy.com/vote/ (ids vb_*). The survey worker only accepts these exact choices.
#   py data_votes.py && py build.py   (build.py copies it to docs/assets/votes.json and writes the worker's Q)
import json
B = ['Toyota', 'Honda', 'Lexus', 'Mazda', 'Subaru', 'Hyundai', 'Kia', 'Ford', 'Chevrolet', 'Nissan', 'Jeep', 'BMW', 'Tesla']
INS = ['State Farm', 'GEICO', 'Progressive', 'Allstate', 'USAA', 'Liberty Mutual', 'Farmers', 'Nationwide']
L = [
 ('brands', 'vl_reliable', 'Most reliable car brand?', B),
 ('brands', 'vl_never', 'Brand you’d never buy again?', ['Nissan', 'Jeep', 'Chrysler / Dodge', 'Ford', 'Chevrolet', 'Volkswagen', 'BMW', 'Land Rover', 'Tesla', 'Kia / Hyundai']),
 ('brands', 'vl_overrated', 'Most overrated car brand?', ['Tesla', 'BMW', 'Mercedes-Benz', 'Jeep', 'Land Rover', 'Audi', 'Toyota', 'Ford']),
 ('brands', 'vl_truckbrand', 'Best truck brand?', ['Ford', 'Chevrolet', 'Ram', 'Toyota', 'GMC', 'Nissan']),
 ('brands', 'vl_luxury', 'Best luxury brand for a used car?', ['Lexus', 'Acura', 'Genesis', 'BMW', 'Mercedes-Benz', 'Audi', 'Infiniti', 'Cadillac']),
 ('models', 'vl_suv15', 'Best used SUV under $15K?', ['Toyota RAV4', 'Honda CR-V', 'Mazda CX-5', 'Subaru Forester', 'Hyundai Tucson', 'Nissan Rogue', 'Ford Escape', 'Chevy Equinox']),
 ('models', 'vl_sedan10', 'Best used car under $10K?', ['Toyota Corolla', 'Honda Civic', 'Toyota Camry', 'Honda Accord', 'Mazda3', 'Hyundai Elantra', 'Lexus ES']),
 ('models', 'vl_pickup', 'Best pickup?', ['Ford F-150', 'Chevy Silverado', 'Ram 1500', 'Toyota Tacoma', 'Toyota Tundra', 'GMC Sierra', 'Nissan Frontier']),
 ('models', 'vl_minivan', 'Best minivan?', ['Honda Odyssey', 'Toyota Sienna', 'Chrysler Pacifica', 'Kia Carnival']),
 ('models', 'vl_ev', 'Best electric car?', ['Tesla Model 3', 'Tesla Model Y', 'Hyundai Ioniq 5', 'Kia EV6', 'Ford Mustang Mach-E', 'Chevy Bolt', 'Rivian R1S']),
 ('models', 'vl_last', 'Which car lasts the longest?', ['Toyota Camry', 'Toyota Corolla', 'Honda Accord', 'Honda Civic', 'Toyota 4Runner', 'Toyota Tacoma', 'Lexus ES', 'Ford F-150']),
 ('years', 'vl_civic', 'Best Honda Civic years?', ['2001–2005', '2006–2011', '2012–2015', '2016–2021', '2022 and newer']),
 ('years', 'vl_camry', 'Best Toyota Camry years?', ['2002–2006', '2007–2011', '2012–2017', '2018–2024', '2025 and newer']),
 ('years', 'vl_f150', 'Best Ford F-150 years?', ['2004–2008', '2009–2014', '2015–2020', '2021 and newer']),
 ('years', 'vl_era', 'Best decade for cars?', ['1990s', '2000s', '2010s', '2020s']),
 ('insurance', 'vl_insbest', 'Best car insurance company?', INS),
 ('insurance', 'vl_insworst', 'Worst car insurance company?', INS),
 ('insurance', 'vl_inspay', 'What do you pay for car insurance a month?', ['Under $100', '$100–150', '$150–200', '$200–300', '$300+']),
 ('buying', 'vl_buyat', 'Best place to buy a used car?', ['CarMax', 'Carvana', 'A local dealer', 'Private seller', 'Facebook Marketplace', 'Auction']),
 ('buying', 'vl_report', 'Which history report do you trust?', ['Carfax', 'AutoCheck', 'A mechanic’s inspection', 'None of them']),
 ('buying', 'vl_nextpower', 'Your next car will be…', ['Gas', 'Hybrid', 'Plug-in hybrid', 'Electric', 'Diesel']),
 ('owning', 'vl_tires', 'Best tire brand?', ['Michelin', 'Goodyear', 'Bridgestone', 'Continental', 'Pirelli', 'Firestone', 'Cooper', 'General']),
 ('owning', 'vl_oil', 'Where do you get your oil changed?', ['The dealer', 'A local mechanic', 'Jiffy Lube', 'Valvoline', 'Take 5', 'Walmart / Costco', 'I do it myself']),
 ('owning', 'vl_gas', 'Best gas station?', ['Costco', 'Buc-ee’s', 'Wawa', 'Sheetz', 'QuikTrip', 'Shell', 'Chevron', 'Exxon / Mobil', 'Speedway']),
]
S = [
 ('money', 'vb_hustle', 'Best side hustle?', ['DoorDash / Uber Eats', 'Uber / Lyft', 'Reselling (eBay, Mercari)', 'Freelancing (Upwork, Fiverr)', 'Tutoring', 'Pet sitting / dog walking', 'YouTube / TikTok', 'Lawn care']),
 ('money', 'vb_1k', 'Best business to start with $1,000?', ['Pressure washing', 'Cleaning', 'Lawn care', 'Car detailing', 'Reselling', 'Vending machines', 'Content creation', 'Dropshipping']),
 ('money', 'vb_lifeset', 'Which would you take?', ['$1 million today', '$5,000 a month for life']),
 ('money', 'vb_invest', 'Where do you invest?', ['Fidelity', 'Vanguard', 'Charles Schwab', 'Robinhood', 'Webull', 'Cash App', 'I don’t invest yet']),
 ('money', 'vb_card', 'Best credit card?', ['Chase Sapphire', 'Amex Gold', 'Capital One Venture', 'Citi Double Cash', 'Discover it', 'Apple Card', 'No credit card']),
 ('work', 'vb_remote', 'Where would you rather work?', ['Fully remote', 'Hybrid', 'In the office', 'My own business']),
 ('work', 'vb_4day', 'Would you take a 4-day week for 10% less pay?', ['Yes', 'No', 'Depends on the job']),
 ('work', 'vb_employer', 'Best big company to work for?', ['Costco', 'Trader Joe’s', 'Chick-fil-A', 'Google', 'Apple', 'Amazon', 'Target', 'Starbucks']),
 ('work', 'vb_degree', 'Is college worth it?', ['Yes', 'Only for some majors', 'Trade school is better', 'No']),
 ('brands', 'vb_fastfood', 'Best fast food chain?', ['Chick-fil-A', 'McDonald’s', 'In-N-Out', 'Wendy’s', 'Taco Bell', 'Chipotle', 'Popeyes', 'Raising Cane’s']),
 ('brands', 'vb_franchise', 'Best franchise to own?', ['McDonald’s', 'Chick-fil-A', 'Subway', 'Taco Bell', 'Dunkin’', 'Crumbl', 'Planet Fitness', 'Jersey Mike’s']),
 ('brands', 'vb_grocery', 'Best grocery store?', ['Costco', 'Aldi', 'Trader Joe’s', 'Walmart', 'H-E-B', 'Publix', 'Kroger', 'Whole Foods']),
 ('brands', 'vb_carrier', 'Best phone carrier?', ['Verizon', 'AT&T', 'T-Mobile', 'Visible', 'Mint Mobile', 'Cricket']),
 ('brands', 'vb_overpriced', 'Most overpriced brand?', ['Apple', 'Starbucks', 'Stanley', 'Nike', 'Disney', 'Tesla', 'Chipotle', 'Supreme']),
 ('business', 'vb_platform', 'Best place to sell online?', ['Amazon', 'Shopify', 'Etsy', 'TikTok Shop', 'eBay', 'Facebook Marketplace', 'My own website']),
 ('business', 'vb_social', 'Best app to grow a business?', ['TikTok', 'Instagram', 'YouTube', 'Facebook', 'LinkedIn', 'X']),
 ('business', 'vb_bank', 'Best bank for a small business?', ['Chase', 'Bank of America', 'Wells Fargo', 'Capital One', 'Mercury', 'Novo', 'A credit union']),
 ('business', 'vb_ceo', 'Most respected CEO?', ['Jensen Huang', 'Tim Cook', 'Elon Musk', 'Warren Buffett', 'Jeff Bezos', 'Mark Zuckerberg', 'Satya Nadella']),
 ('business', 'vb_hard', 'Hardest part of running a business?', ['Getting customers', 'Money / cash flow', 'Hiring', 'Taxes and legal', 'Staying consistent', 'Pricing']),
]
CAT = {'lemon': {'brands': 'Brands', 'models': 'Models', 'years': 'Years', 'insurance': 'Insurance', 'buying': 'Buying', 'owning': 'Owning'},
       'bs': {'money': 'Money', 'work': 'Work', 'brands': 'Brands', 'business': 'Business'}}
out = {'cats': CAT, 'lemon': [dict(id=i, cat=c, q=q, a=a) for c, i, q, a in L], 'bs': [dict(id=i, cat=c, q=q, a=a) for c, i, q, a in S]}
# head-to-head polls (11-03, Elijah: "Chevy vs Ford with two 3D pillars that adjust to who's winning, with a truck on each pillar"):
# vote.js shows them on top of the vote page as two pillars; img = cutouts from Wikimedia Commons (credits shown under the pillars)
out['lemon'].insert(0, dict(id='vl_chevyford', cat='brands', q='Chevy or Ford?', a=['Chevy', 'Ford'], duel={
    'Chevy': {'img': '/assets/vote/chevy.webp', 'color': '#c9a227', 'credit': 'Ghostofakina, CC BY-SA 4.0', 'page': 'https://commons.wikimedia.org/wiki/File%3A2019_Chevrolet_Silverado_1500_Crew_Cab_LT_%28front%29%2C_10.20.19.jpg'},
    'Ford': {'img': '/assets/vote/ford.webp', 'color': '#1f4ea8', 'credit': 'Kevauto, CC BY-SA 4.0', 'page': 'https://commons.wikimedia.org/wiki/File:2018_Ford_F-150_Crew_Cab_front_5.26.18.jpg'}}))
for k in ('lemon', 'bs'):
    ids = [p['id'] for p in out[k]]; assert len(ids) == len(set(ids))
    for p in out[k]: assert len(p['a']) == len(set(p['a'])) and all(len(x) < 60 for x in p['a']) and p['cat'] in CAT[k]
json.dump(out, open('data/votes.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('votes:', len(L), 'lemon,', len(S), 'business study')
