import discord
import asyncio
from discord.ext import commands
from nba_api.stats.endpoints import scoreboard
from nba_api.stats.static import teams
from nba_api.stats.library.parameters import GameDate
import pandas as pd
import json

class nba(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("nba is ready to go")

    def make_embed(self, title, message):
        return discord.Embed(title=title, description=message)

    # returns the games/scores of a given date
    @commands.command()
    async def scores(self, ctx, *, date=GameDate.default):
        # default date is the current date
        try:
            score = scoreboard.Scoreboard(game_date=date)
            result = await self.get_scores(score)
            if result == '':
                await ctx.send('No games were played that day')
            else:
                embed = discord.Embed(title="Scores for {}".format(date), description=result)
                await ctx.send(embed=embed)
        except:
            await ctx.send('Invalid date format, make sure the format is "YYYY-MM-DD" ')

    # formats the output for scores
    async def get_scores(self, score):
        result = ''
        line_score = score.line_score
        ls_df = line_score.get_data_frame()
        if not ls_df.empty:
            team_points = ls_df[['TEAM_ID', 'PTS']]
            for x in range(0, len(team_points), 2):
                try:
                    away_team = teams.find_team_name_by_id(ls_df['TEAM_ID'][x])['full_name']
                    home_team = teams.find_team_name_by_id(ls_df['TEAM_ID'][x + 1])['full_name']
                # handles case where teams are not in the list of current teams i.e. Team LeBron, West All-Stars
                except:
                    away_team = ls_df['TEAM_CITY_NAME'][x] + ' ' + ls_df['TEAM_ABBREVIATION'][x]
                    home_team = ls_df['TEAM_CITY_NAME'][x + 1] + ' ' + ls_df['TEAM_ABBREVIATION'][x+1]
                away_points = ls_df['PTS'][x]
                home_points = ls_df['PTS'][x + 1]
                away_win = ''
                home_win = ''
                if home_points > away_points:
                    home_win = '**'
                else:
                    away_win = '**'
                result += '{}{}  {}{} - {}{}  {}{}\n'.format(away_win,
                                                             away_team,
                                                             away_points, away_win, home_win, home_points,
                                                             home_team,
                                                             home_win)
        return result

    # returns the careers stats of a given player
    @commands.command()
    async def pcareerstat(self, ctx, *, player_name=''):
        from nba_api.stats.endpoints import playercareerstats
        from nba_api.stats.static import players

        player_dict = players.get_players()

        try:
            player_name = player_name.lower()
            player_info = [player for player in player_dict if player['full_name'].lower() == player_name][0]
            play_id = player_info['id']
            career_stats = playercareerstats.PlayerCareerStats(player_id=play_id)
            career_tot = career_stats.career_totals_regular_season.get_data_frame()
            embed = discord.Embed(title='Career Stats for {}:\n'.format(player_info['full_name']))
            result = '```'
            for cat in range(3,len(career_tot.columns)):  # filters out the player, league, and team ID
                category = career_tot.columns[cat]
                result += "{}: {}\n".format(category, career_tot[category][0])
            result += '```'
            embed.description = result
            await ctx.send(embed=embed)
        except:
            await ctx.send('Couldn\'t find the player.')


    # returns the careers stats of a given player
    @commands.command()
    async def pseasonstat(self, ctx, *input):
        from nba_api.stats.endpoints import playercareerstats
        from nba_api.stats.static import players
        from nba_api.stats.static import teams

        # check if the input is first name, last name, and year (beginning of season)
        if len(input) < 3:
            await ctx.send('Please provide the player\'s full name and year at the beginning of the season (in that order)')
        else:
            player_name = input[0] + ' ' + input[1]
            player_name = player_name.lower()
            season = input[2] + '-' + str(int(input[2]) + 1)[-2:]  # configure the season year to fit the API arguments
            player_dict = players.get_players()
            # check if the user inputted a valid player
            try:
                player_info = [player for player in player_dict if player['full_name'].lower() == player_name][0]
                play_id = player_info['id']
                player_career_stats = playercareerstats.PlayerCareerStats(player_id=play_id)
                # check if the user inputted a valid season
                try:
                    season_tot = player_career_stats.season_totals_regular_season.get_data_frame()
                    season_info = season_tot[season_tot['SEASON_ID'] == season]
                    categories = season_info.columns
                    stats = season_info.values
                    embed = discord.Embed(title='{} Season Stats for {}:\n'.format(season, player_info['full_name']))
                    team_id = stats[0][categories.get_loc('TEAM_ID')]  # gets the player's team for the given season
                    player_team = teams.find_team_name_by_id(team_id)
                    result = '```TEAM: {}\n'.format(player_team['full_name'])
                    for cat in range(5, len(categories)):  # filters out the player, league, and team ID
                        result += '{}: {}\n'.format(categories[cat], stats[0][cat])
                    result += '```'
                    embed.description = result
                    await ctx.send(embed=embed)
                except:
                    await ctx.send('The player did not play in that season')
            except:
                await ctx.send('Couldn\'t find the player.')

    # returns the league standings
    @commands.command()
    async def standings(self, ctx):
        from nba_api.stats.endpoints import leaguestandings
        standings = leaguestandings.LeagueStandings()
        stand_df = standings.get_data_frames()[0]
        east_stand = stand_df[stand_df['Conference'] == 'East']
        west_stand = stand_df[stand_df['Conference'] == 'West']

        embed = discord.Embed(title='Current Standings:')

        east_result = ''
        for i, row in enumerate(east_stand.itertuples(), 1):
            east_result += '`{:<3} {:23} {:5}`\n'.format(i, teams.find_team_name_by_id(row.TeamID)['full_name'], row.Record)
        embed.add_field(name='Eastern Conference', value=east_result, inline=True)
        west_result = ''
        for i, row in enumerate(west_stand.itertuples(), 1):
            west_result += '`{:<3} {:23} {:5}`\n'.format(i, teams.find_team_name_by_id(row.TeamID)['full_name'], row.Record)
        embed.add_field(name='Western Conference', value=west_result, inline=True)
        await ctx.send(embed=embed)

    # returns the league leaders for a given statistic
    @commands.command()
    async def leagueleaders(self, ctx, stat=''):
        from nba_api.stats.endpoints import homepageleaders
        from nba_api.stats.library.parameters import PlayerOrTeam

        stat_cat = await self.get_stat_cat(stat.upper())
        if stat_cat is None:
            await ctx.send('Please input a valid category. The categories are: PTS, AST, REB, and BLK')
        else:
            leaders = homepageleaders.HomePageLeaders(player_or_team=PlayerOrTeam.player, stat_category=stat_cat)
            leaders_df = leaders.get_data_frames()[0]
            embed = discord.Embed(title='League Leaders for {} Per Game'.format(stat.upper()))
            result = '`{:<4}  {:23} {:>5}`\n'.format('Rank', 'Name', stat.upper())
            for index, row in leaders_df.iterrows():
                result += '`{:<4}  {:23} {:5}`\n'.format(row.RANK, row.PLAYER, row[stat.upper()])
            embed.description = result
            await ctx.send(embed=embed)

    # returns the API category parameter based on string input
    async def get_stat_cat(self, category):
        from nba_api.stats.library.parameters import StatCategory

        return {
            'PTS': StatCategory.points,
            'AST': StatCategory.assists,
            'REB': StatCategory.rebounds,
            'BLK': StatCategory.defense

        }.get(category, None)

    # adds a player to a user's favorites list
    @commands.command()
    async def fav(self, ctx, *, player_name=''):
        from nba_api.stats.static import players

        player_dict = players.get_players()
        try:
            player_name = player_name.lower()
            player_info = [player for player in player_dict if player['full_name'].lower() == player_name][0]
            player_name = player_info['full_name']
            user_id = str(ctx.author.id)
            with open('user_favorites.json') as f:
                favorites = json.load(f)
            if not favorites or user_id not in favorites:
                favorites[user_id] = [player_name]
            else:
                fav_list = favorites[user_id]
                fav_list.append(player_name)
                favorites[user_id] = fav_list
            with open('user_favorites.json', 'w') as f:
                json.dump(favorites, f, indent=4)
            await ctx.send("{} has been added to your favorites list.".format(player_name))
        except:
            await ctx.send('Couldn\'t find the player.')


def setup(client):
    client.add_cog(nba(client))