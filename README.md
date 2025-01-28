# rent-radar

---

RentRadar is a tool to detect and report landlord price gouging (specifically in Los Angeles in the aftermath of the 2025 fires). 


## Setup

---

1. Install the following tools if you don't already have them:
    - [PyEnv](
    - [Poetry](https://python-poetry.org/docs/) - requires Python 3.11+ 
2. Run the following commands to install dependencies:
    ```shell
    pyenv local <python3-version>
    poetry install 
    ```
3. Set your Rent Cast API token as an environment variable or in a `.env` file.
    ```shell
    export RENT_RADAR_RENT_CAST_API_KEY=<your-api-key>
    ```
4. Run the following command to run the RentRadar tool:
    ```shell
    poetry run python rent_radar/main.py
    ```

## How it Works 

---

1. RentRadar uses the [Rent Cast API](https://developers.rentcast.io/reference/rental-listings-long-term) to identify active rental listings for the cities in LA County. 
2. The current price of each listing is compared to the Small Area Fair Market Rate (SAFMR) for the area based on its zip code and the number of bedrooms. If the current price exceeds 160% of the SAFMR, the listing is flagged as a potential violation of the law.
3. If the listing has a price history, RentRadar will further check to see if there has been a 10% increase since before January 6, 2025. If so, the listing will be flagged as a potential violation of the law. 
4. All of the potential violations are then stored in a SQL Database with detailed information about the listing, the type of potential violation (either `price_increase` or `fmr_rate`), and the date that the listing data was accessed.

## Rent Gouging FAQs
Credit: [The Rent Brigade](https://docs.google.com/document/d/1hn0IKHW4kjbthblhoEA4MaqhgIMHZALUqEUj-G55CSI/edit?tab=t.0)

---

### What is rent gouging?
Rent gouging is the predatory practice of landlords exploiting tenants by demanding inflated rent prices. Legally, it occurs when landlords raise rents beyond the allowed limit during a declared State of Emergency. Since January 7, 2025, LA County has been under such a declaration, which prohibits landlords from increasing rents by more than 10% of their pre-listed price as of  one year before. Specific rules also apply to new listings and short-term rentals (STRs). 

### Which law prohibits rent gouging?
Rent gouging during a state of emergency is prohibited under Penal Code Section 396, which bans landlords from drastically inflating rents and exploiting tenants in crisis. The law applies to all types of rentals, including single-family homes, apartments, condos, and short-term rentals (STRs). 

### How does the law apply to different types of rentals? 

**Previously listed rentals:** Rent increases cannot exceed 10% of the most recent price advertised or charged in the year before the emergency.

**Newly listed rentals or relisted rentals:** For rentals not listed for rent since before January 7, 2024, the price cannot exceed 160% of the Fair Market Rent (FMR) for the ZIP code. Find the FMR for your area on the HUD website.

**Short-term rental platforms like Airbnb and VRBO and hotels/motels:** 
* Daily rental rates cannot increase by more than 10%
* If a short-term rental converts to a monthly or long-term rental after the emergency declaration, the rent cannot exceed 160% of the FMR set by HUD
* Rent increases cannot exceed 10% of the most recent price advertised or charged in the year before the emergency

**What if the rental is furnished?**
If furniture is added to a rental that was previously unfurnished, landlords may increase the price by up to an additional 5% above the 10% limit—but no more. This applies to both short-term and long-term rentals.. 

### What practices are prohibited under the rent gouging law?
* Justifying illegal rent increases by adding services like cleaning or utilities
* Charging higher rents because an insurance company is paying
* Accepting an illegally high amount of rent even if a tenant offers to pay the higher amount (no bidding wars)

### How long are the protections in effect?
Rent gouging protections remain in place until January 7, 2026, per Governor Newsom’s Executive Order N-4-25.x

### What are the penalties for rent gouging?
According to the law: 
Fines of up to $10,000
Up to one year in jail
