"""Synthetic FIR generator with labelled modus-operandi (MO) clusters.

Each MO has 6 "facts", each with 3 paraphrases. A FIR picks 3-5 facts (so two FIRs of the same MO
only partly overlap), paraphrases them randomly, sometimes borrows a fact from another MO, and
adds generic filler. Locations, names, dates and amounts are random and shared across MOs, so they
carry no signal. Two MOs are held out as NOVEL to test that the linker does not force a link.

    python generate_firs.py --per-cluster 50
"""
import argparse, json, random

NOVEL = ["fake_job_offer", "transformer_theft"]

CLUSTERS = {
"chain_snatching": [
 ["Two unidentified men arrived on a motorcycle and approached her from behind.",
  "The accused, two persons on a bike, came from behind and slowed down near her.",
  "A motorcycle with two riders followed her along the road and stopped alongside."],
 ["One of them snatched her gold chain from her neck and pulled it away forcefully.",
  "The pillion rider grabbed the gold mangalsutra she was wearing and tore it off.",
  "Her gold necklace was yanked off her neck in a sudden attack."],
 ["Both riders were wearing helmets so their faces could not be seen.",
  "The men had covered their faces with helmets and scarves.",
  "Their faces were hidden behind helmets and the number plate of the motorcycle was smeared with mud."],
 ["The complainant was walking alone on the road in the evening when the incident occurred.",
  "She was returning home on foot from the market at the time.",
  "She was out for an evening walk when this happened."],
 ["They sped away towards the main road before anyone could react.",
  "The accused fled at high speed through the adjoining lanes.",
  "The motorcycle disappeared in the traffic within seconds."],
 ["The chain weighed about {n} grams and is valued at approximately Rs {v}.",
  "The stolen ornament was around {n} grams, worth about Rs {v}.",
  "The loss is a gold chain of roughly {n} grams costing about Rs {v}."]],
"phone_snatching": [
 ["Two youths riding a scooter came up from behind the complainant.",
  "Two young men on a two-wheeler approached suddenly from behind.",
  "A pair of boys on a bike drove close to the complainant."],
 ["One of them snatched the mobile phone from the complainant's hand while he was talking.",
  "The pillion rider grabbed the smartphone that the complainant was holding and pulled it away.",
  "The phone was snatched from the complainant's hand near the road."],
 ["Their faces were partly covered with handkerchiefs.",
  "Both wore masks and caps.",
  "They had tied cloth around their faces."],
 ["The complainant was standing at the roadside checking the phone.",
  "The complainant was walking to the bus stop while on a call.",
  "The complainant was waiting for an auto-rickshaw when this occurred."],
 ["The youths escaped through narrow lanes on the scooter.",
  "They rode off at high speed and could not be chased.",
  "They quickly disappeared into the traffic."],
 ["The phone, a {phone} model, is worth about Rs {amt}.",
  "The stolen mobile is a {phone} handset valued at roughly Rs {amt}.",
  "The loss is a {phone} phone costing around Rs {amt}."]],
"house_burglary": [
 ["The complainant and family had gone out of town for a few days and the house was locked.",
  "The house remained locked as the family was away at a relative's place.",
  "The residents were away for a wedding and the flat was kept locked."],
 ["On return, the main door lock was found broken.",
  "The grill of the rear window had been cut and the door was found open.",
  "Entry was gained by breaking the lock of the front door."],
 ["The bedroom cupboards were opened and clothes and papers were scattered everywhere.",
  "The almirah had been ransacked and its contents lay strewn on the floor.",
  "All rooms were found in disorder with the lockers forced open."],
 ["Gold ornaments of about {tola} tolas and cash of Rs {amt} were missing.",
  "Jewellery and cash amounting to roughly Rs {v} were stolen.",
  "Missing items include gold jewellery and Rs {amt} in cash."],
 ["The neighbours heard noises late at night but assumed nothing was wrong.",
  "The theft appears to have been committed during the night when the street was empty.",
  "Nobody saw anything but the incident likely occurred after midnight."],
 ["There is no CCTV camera in the lane.",
  "No security guard was posted in the building.",
  "The locality is poorly lit at night."]],
"shop_burglary": [
 ["The complainant runs a shop and had closed it at night as usual.",
  "The shop was shut at closing time and the shutter was locked.",
  "The complainant closed his store around 9 pm and locked the shutter."],
 ["In the morning the shutter lock was found cut with a cutter.",
  "The shutter had been lifted by breaking the padlocks.",
  "The shop's lock was found broken and the shutter partly open."],
 ["The cash counter drawer was empty and Rs {amt} kept there was missing.",
  "The day's collection of Rs {amt} was stolen from the drawer.",
  "Cash of about Rs {amt} was taken from the counter."],
 ["Goods and stock worth about Rs {v} were also removed from the shelves.",
  "Electronic items and stock valued around Rs {v} are missing.",
  "A significant amount of merchandise was taken."],
 ["The CCTV recorder installed in the shop was also removed by the thieves.",
  "The camera recorder was taken away to destroy evidence.",
  "The thieves had damaged the CCTV camera and taken its recorder."],
 ["Nearby shopkeepers noticed nothing suspicious during the night.",
  "The market area has no night watchman.",
  "Similar thefts have occurred in the market recently."]],
"atm_skimming": [
 ["The complainant withdrew cash from an ATM near {loc2} a few days earlier.",
  "The complainant had used a stand-alone ATM kiosk to withdraw money.",
  "The complainant last used his debit card at an ATM."],
 ["Later, several unauthorised withdrawals were made from the account through ATMs in another city.",
  "Multiple cash withdrawals totalling Rs {amt} were made without his knowledge.",
  "SMS alerts showed repeated transactions of Rs {amt} in total though the card was with the complainant."],
 ["The card was in the complainant's possession throughout and he never shared his PIN.",
  "He did not share the PIN with anyone.",
  "The debit card had never left his possession."],
 ["It is suspected that a skimming device was fitted on the card slot of the ATM.",
  "A card-cloning device and a hidden camera near the keypad are suspected.",
  "The bank has said that the card data may have been copied at the ATM."],
 ["The complainant blocked the card immediately after noticing the alerts.",
  "A complaint has been lodged with the bank customer care.",
  "He informed the bank as soon as he saw the messages."],
 ["Other customers of the same ATM have reported similar losses.",
  "The ATM had no security guard.",
  "Several similar complaints have been received about the same machine."]],
"otp_fraud": [
 ["The complainant received a call from a person claiming to be a bank executive.",
  "An unknown caller posing as a representative of the bank phoned the complainant.",
  "The complainant got a call from someone saying he was from the bank's KYC department."],
 ["The caller said the account would be blocked unless KYC was updated immediately.",
  "He said the debit card was about to expire and needed verification.",
  "The caller created urgency by saying the account would be frozen."],
 ["He asked for the OTP received on the phone and the complainant shared it.",
  "The complainant shared card details and the OTP as asked.",
  "The complainant was made to read out the OTP received by SMS."],
 ["Immediately afterwards Rs {amt} was debited from the account.",
  "An amount of Rs {amt} was withdrawn within minutes.",
  "The account balance dropped by Rs {amt} shortly after the call."],
 ["The caller also sent a link and asked the complainant to install a screen-sharing app.",
  "He asked the complainant to download a remote access application.",
  "A suspicious link was sent by SMS which the complainant clicked."],
 ["The number was switched off afterwards.",
  "The mobile number used by the caller is now unreachable.",
  "The complainant tried calling back but the number was switched off."]],
"vehicle_theft": [
 ["The complainant parked his two-wheeler in front of his house as usual.",
  "The bike was parked in the society parking area.",
  "The motorcycle was parked outside a hospital while he visited a relative."],
 ["When he returned the vehicle was not at the spot.",
  "In the morning the vehicle was missing.",
  "After an hour the complainant found that the vehicle was gone."],
 ["The handle lock appears to have been broken.",
  "The thieves probably broke the handle lock and started it by joining wires.",
  "It is suspected the ignition wires were bypassed."],
 ["The vehicle is a {bike} model registered in Nagpur.",
  "The stolen vehicle is a {bike} bike bought last year.",
  "It is a {bike} two-wheeler valued at about Rs {v}."],
 ["No CCTV footage is available from the area.",
  "The parking area has no camera.",
  "Nearby cameras did not cover the spot."],
 ["The complainant searched the neighbourhood but could not find it.",
  "He also checked with nearby friends and relatives.",
  "Similar bike thefts have occurred in the locality."]],
"marketplace_fraud": [
 ["The complainant found an advertisement on an online classifieds app offering a {item} at a low price.",
  "A listing on a resale website offered a {item} at a cheap price.",
  "The complainant saw a post on social media selling a {item}."],
 ["The seller claimed to be an army officer being transferred and needing a quick sale.",
  "The seller said he was posted elsewhere and demanded advance payment.",
  "The seller insisted on advance payment to reserve the item."],
 ["The complainant transferred Rs {amt} through UPI as advance.",
  "An amount of Rs {amt} was paid via UPI to the seller.",
  "He paid Rs {amt} online to confirm the booking."],
 ["The seller then asked for more money for delivery charges and insurance.",
  "Additional charges were demanded for courier and taxes.",
  "He kept demanding further payment on different pretexts."],
 ["Afterwards the seller stopped responding and blocked the complainant's number.",
  "The phone was switched off and the profile was deleted.",
  "The complainant was blocked on all platforms."],
 ["The item was never delivered.",
  "The complainant later realised the advertisement was fake.",
  "The photos used in the advertisement were taken from the internet."]],
"truck_cargo_theft": [
 ["The complainant, a truck driver, had parked his loaded truck at a roadside dhaba for the night.",
  "The goods truck was halted near a highway dhaba for rest.",
  "The driver stopped at a highway rest stop and slept in the cabin."],
 ["The tarpaulin covering the load was found cut in the morning.",
  "The rope and tarpaulin of the truck had been slashed.",
  "The cover of the loading area was cut open."],
 ["Bags of goods worth about Rs {v} were missing from the truck.",
  "Part of the consignment valued around Rs {v} was stolen.",
  "Several sacks were removed from the cargo."],
 ["The driver did not wake up as he was asleep in the cabin.",
  "The driver says he heard nothing.",
  "The driver reportedly felt drowsy that night."],
 ["It is believed the theft was carried out by a gang that follows trucks on the highway.",
  "A gang operating on this highway stretch is suspected.",
  "Similar cargo thefts have been reported at highway stops recently."],
 ["The truck owner has informed the transport company.",
  "The goods belong to a trader in {loc2}.",
  "The delivery was to be made at {loc2}."]],
"pickpocketing": [
 ["The complainant was travelling in a crowded city bus.",
  "The incident took place in a crowded market during a festival.",
  "The complainant was standing in a crowded queue at a railway station."],
 ["A group of three or four persons pushed against him while boarding.",
  "Several men jostled the complainant in the crowd.",
  "A gang of youths created a crowd around him."],
 ["His wallet was removed from the back pocket without his noticing.",
  "The complainant later found his purse missing from the bag.",
  "The bag was found cut with a blade and the purse missing."],
 ["The wallet contained Rs {amt} in cash, ATM cards and ID documents.",
  "Cash of Rs {amt} along with the Aadhaar card and licence was inside.",
  "The stolen purse held Rs {amt} and other important cards."],
 ["The complainant realised the theft only after getting down at the stop.",
  "He noticed the loss when he tried to pay.",
  "He noticed the missing items after leaving the crowd."],
 ["The group left the bus at the next stop.",
  "The persons disappeared quickly in the crowd.",
  "The suspects got off midway."]],
"fake_job_offer": [
 ["The complainant received a message on WhatsApp offering a work-from-home job.",
  "A recruiter contacted the complainant through a job portal offering a well-paid position.",
  "The complainant applied through a website for an overseas job."],
 ["He was asked to pay a registration fee of Rs {amt}.",
  "A processing fee of Rs {amt} was demanded for confirming the appointment.",
  "Money was demanded for training material and documents."],
 ["An appointment letter with a company logo was sent by email.",
  "The offer letter appeared genuine with the company's letterhead.",
  "He was given a fake joining letter."],
 ["Later further payment was asked for visa and medical formalities.",
  "The recruiter demanded more money for uniform and security deposit.",
  "More amounts were demanded on various pretexts."],
 ["After the payments the recruiter stopped taking calls.",
  "The website and contact numbers stopped working.",
  "The complainant was blocked on the chat."],
 ["Several other job seekers were also cheated.",
  "The company named in the letter does not exist.",
  "The company denied having offered any such job."]],
"transformer_theft": [
 ["The transformer installed near the farm field was found damaged in the morning.",
  "The electricity distribution transformer at the outskirts of the village was opened.",
  "The complainant, a farmer, found the transformer near his field vandalised."],
 ["Copper coils and winding were removed from inside.",
  "The copper wires of the transformer were stolen.",
  "Valuable copper parts had been taken out."],
 ["The transformer oil was spilled on the ground.",
  "Oil was found drained around the base.",
  "The cooling oil was found leaked all around."],
 ["Because of this the power supply to the fields has been cut.",
  "The village has been without electricity since.",
  "The irrigation pumps stopped working."],
 ["The theft appears to have been done at night using tools and a vehicle.",
  "Tyre marks of a heavy vehicle were seen near the spot.",
  "Footprints of several people were seen."],
 ["The electricity board had been informed.",
  "The loss is estimated at Rs {v}.",
  "The area is isolated with no one around at night."]],
}

# MOs that genuinely resemble each other in real records; borrowed facts come from these more often
SIBLINGS = {
    "chain_snatching": ["phone_snatching"], "phone_snatching": ["chain_snatching", "pickpocketing"],
    "house_burglary": ["shop_burglary"], "shop_burglary": ["house_burglary"],
    "atm_skimming": ["otp_fraud"], "otp_fraud": ["atm_skimming", "marketplace_fraud", "fake_job_offer"],
    "marketplace_fraud": ["otp_fraud", "fake_job_offer"], "fake_job_offer": ["marketplace_fraud", "otp_fraud"],
    "vehicle_theft": ["truck_cargo_theft"], "truck_cargo_theft": ["vehicle_theft"],
    "pickpocketing": ["phone_snatching"],
}

LOCS = ["Sitabuldi", "Dharampeth", "Sadar", "Itwari", "Manish Nagar", "Pratap Nagar", "Wardhaman Nagar",
        "Hingna", "Kamptee Road", "Trimurti Nagar", "Besa", "Manewada", "Gittikhadan", "Ajni", "Civil Lines",
        "Jaripatka", "Nandanvan", "Khamla", "Bajaj Nagar", "Koradi Road"]
NAMES = ["Rajesh Patil", "Sunita Deshmukh", "Amit Verma", "Priya Kulkarni", "Mohan Gupta", "Kavita Joshi",
         "Sanjay Bhoyar", "Neha Thakre", "Ravi Meshram", "Anita Raut", "Vikas Wankhede", "Pooja Sharma"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
PHONES = ["Samsung", "Redmi", "Vivo", "Realme", "OnePlus", "Oppo"]
BIKES = ["Honda Activa", "Hero Splendor", "Bajaj Pulsar", "TVS Apache", "Suzuki Access"]
ITEMS = ["laptop", "camera", "sofa set", "scooter", "refrigerator"]

OPENERS = [
 "On {date} at about {time}, complainant {name}, aged {age}, of {loc}, came to the police station to report an incident.",
 "The complainant, {name} ({age} years), residing at {loc}, states that the following occurred on {date} around {time}.",
 "A complaint was received from {name}, aged {age}, a resident of {loc}, regarding an incident on {date} at approximately {time}.",
]
LOC_SENTS = ["The incident took place near {loc2}.", "The spot is close to {loc2}.", "This happened in the {loc2} area."]
CLOSERS = ["The accused could not be identified.",
           "The complainant requests that a case be registered and the accused be traced.",
           "No one else witnessed the incident.",
           "The complainant is ready to identify the accused if caught.",
           "A written complaint was submitted at the police station."]


def make_fir(cluster, rng):
    facts = CLUSTERS[cluster]
    idx = sorted(rng.sample(range(len(facts)), rng.randint(2, 4)))
    if rng.random() < 0.3:
        rng.shuffle(idx)
    sents = [rng.choice(facts[i]) for i in idx]
    for _ in range(rng.choice([0, 0, 1, 1, 2])):  # borrowed facts from other MOs (noise)
        pool = SIBLINGS.get(cluster, []) if rng.random() < 0.6 else []
        other = rng.choice(pool or [c for c in CLUSTERS if c != cluster])
        sents.insert(rng.randrange(len(sents) + 1), rng.choice(rng.choice(CLUSTERS[other])))
    if rng.random() < 0.6:
        sents.insert(0, rng.choice(LOC_SENTS))
    loc = rng.choice(LOCS)
    vals = dict(
        date=f"{rng.randint(1, 28)} {rng.choice(MONTHS)} 2026",
        time=f"{rng.randint(1, 12)}:{rng.choice(['05', '15', '30', '45'])} {rng.choice(['am', 'pm'])}",
        name=rng.choice(NAMES), age=rng.randint(22, 70), loc=loc,
        loc2=rng.choice([l for l in LOCS if l != loc]),
        n=rng.randint(10, 60), tola=rng.randint(2, 8),
        amt=rng.randrange(2000, 100000, 500), v=rng.randrange(10000, 300000, 1000),
        phone=rng.choice(PHONES), bike=rng.choice(BIKES), item=rng.choice(ITEMS))
    text = " ".join([rng.choice(OPENERS)] + sents + rng.sample(CLOSERS, rng.randint(1, 2)))
    return text.format(**vals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cluster", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="firs.json")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    data = [{"mo": c, "text": make_fir(c, rng)} for c in CLUSTERS for _ in range(a.per_cluster)]
    rng.shuffle(data)
    for i, d in enumerate(data):
        d["id"] = f"FIR-{i:04d}"
    json.dump({"novel": NOVEL, "firs": data}, open(a.out, "w"), indent=1)
    print(f"wrote {len(data)} FIRs, {len(CLUSTERS)} MOs ({len(NOVEL)} held out as novel) -> {a.out}")
    print("example:", data[0]["mo"], "|", data[0]["text"])


if __name__ == "__main__":
    main()
