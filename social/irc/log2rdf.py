import percolation as P, social as S, numpy as n, pickle, dateutil, nltk as k, os, datetime, shutil, rdflib as r, codecs
from percolation.rdf import NS, U, a, po, c
class LogPublishing:
    def __init__(self,snapshoturi,snapshotid,filename="foo.txt",\
            data_path="../data/irc/",final_path="./irc_snapshots/",umbrella_dir="irc_snapshots/"):
        c(snapshoturi,snapshotid,filename)
        isego=False
        isgroup=True
        isfriendship=False
        isinteraction=True
        hastext=True
        interactions_anonymized=False

        irc_graph="social_log"
        meta_graph="social_irc_meta"
        social_graph="social_irc"
        P.context(irc_graph,"remove")
        P.context(meta_graph,"remove")
        final_path_="{}{}/".format(final_path,snapshotid)
        online_prefix="https://raw.githubusercontent.com/OpenLinkedSocialData/{}master/{}/".format(umbrella_dir,snapshotid)
        locals_=locals().copy(); del locals_["self"]
        for i in locals_:
            exec("self.{}={}".format(i,i))
        self.rdfLog()
        self.makeMetadata()
        self.writeAllIRC()
    def rdfLog(self):
        with codecs.open(self.data_path+self.filename,"rb","iso-8859-1")  as f:
            text=textFix(f.read())
        # msgregex=r"\[(\d{2}):(\d{2}):(\d{2})\] \* ([^ ?]*)[ ]*(.*)" # DELETE ???
        #rmessage= r"\[(\d{2}):(\d{2}):(\d{2})\] \<(.*?)\>[ ]*(.*)" # message
        # lista arquivos no dir
        rdate=r"(\d{4})(\d{2})(\d{2})" # date
        rsysmsg=r"(\d{4})\-(\d{2})\-(\d{2})T(\d{2}):(\d{2}):(\d{2})  \*\*\* (\S+) (.*)" # system message (?)
        rmsg=r"(\d{4})\-(\d{2})\-(\d{2})T(\d{2}):(\d{2}):(\d{2})  \<(.*?)\> (.*)" # message
        messages=re.findall(rmsg,t)
        system_messages=re.findall(rsysmsg,t)
        NICKS=set([Q(i[-2]) for i in messages]+[Q(i[-2]) for i in system_messages])
        triples=[]
        for nick in NICKS:
            useruri=P.rdf.ic(po.Participant,"{}-{}".format(self.snapshoturi,nick),self.irc_graph,self.snapshoturi)
            triples+=[
                    (useruri,po.nick,nick),
                    ]
        messageids=set()
        for message in messages:
            year, month, day, hour, minute, second, nick, text=message
            nick=Q(nick)
            # achar direct message com virgula! TTM

            tokens=k.word_tokenize(text)
            tokens=[i for i in tokens if i not in set(string.punctuation)]
            direct_nicks=[] # for directed messages at
            mention_nicks=[] # for mentioned fellows
            direct=1
            for token in tokens:
                if token not in NICKS:
                    direct=0
                else:
                    if direct:
                        direct_nicks+=[token]
                    else:
                        mendion_nicks+=[token]

            datetime_=datetime.datetime(*[int(i) for i in (year,month,day,hour,minute,second)])
            timestamp=datetime_.isoformat()
            messageid="{}-{}-{}".format(snapshoturi,nick,timestamp)
            while messageid in messageids:
                messageid+='_r_%05x' % random.randrange(16**5)
            messageids.add(messageid)
            messageuri=P.rdf.ic(po.IRCMessage,messageid,context=self.irc_graph,self.snapshoturi)
            useruri=po.Participant+"#{}-{}".format(self.snapshoturi,nick)
            triples+=[
                     (messageuri,po.author,useruri),
                     (messageuri,po.systemMessage,False),
                     (messageuri,po.sentAt,datetime_),
                     ]
            if text:
                triples+=[
                         (messageuri,po.messageText,text),
                         ]
            text_=text[text.index(nicks2[-1])+len(nicks2[-1])+1:].lstrip()
            if text_:
                triples+=[
                         (messageuri,po.cleanMessageText,text_),
                         ]
            else:
                triples+=[
                         (messageuri,po.emptyMessage,True),
                         ]
            for nick in direct_nicks:
                useruri2=po.Participant+"#{}-{}".format(snapshoturi,nick)
                triples+=[
                         (messageuri,po.directedTo,useruri2),
                         ]
            for nick in mention_nicks:
                useruri2=po.Participant+"#{}-{}".format(snapshoturi,nick)
                triples+=[
                         (messageuri,po.mentions,useruri2),
                         ]
        messageids=set()
        for message in system_messages:
            year, month, day, hour, minute, second, nick, text=message
            nick=Q(nick)
            useruri=po.Participant+"#{}-{}".format(self.snapshot,nick))

            datetime_=datetime.datetime(*[int(i) for i in (year,month,day,hour,minute,second)])
            timestamp=datetime_.isoformat()
            messageid="{}-{}".format(self.snapshotid,timestamp)
            while messageid in messageids:
                messageid+='_r_%05x' % random.randrange(16**5)
            messageids.update([messageid])
            messageuri=P.rdf.ic(po.IRCMessage,messageid,context=self.irc_graph,self.snapshoturi)
            triples+=[
                    (messageuri,po.impliedUser,useruri)
                    (messageuri,po.sentAt,datetime_)
                    (messageuri,po.systemMessage,True)
                    ]
            if text:
                triples+=[
                        (messageuri,po.messageText,text)
                        ]
        P.add(triples,context=self.irc_graph)

    def makeMetadata(self):
        triples=P.get(self.snapshoturi,None,None,self.social_graph)
        for rawfile in P.get(self.snapshoturi,po.rawFile,None,self.social_graph,strict=True,minimized=True):
            triples+=P.get(rawfile,None,None,self.social_graph)
        self.totalchars=sum(self.nchars_all)
        self.mcharsmessages=n.mean(self.nchars_all)
        self.dcharsmessages=n.std(self.nchars_all)
        self.totaltokens=sum(self.ntokens_all)
        self.mtokensmessages=n.mean(self.ntokens_all)
        self.dtokensmessages=n.std(self.ntokens_all)
        P.add(triples,context=self.meta_graph)
        triples=[
                (self.snapshoturi, po.nParticipants,           self.nparticipants),
                (self.snapshoturi, po.nMessages,                 self.nmessages),
                (self.snapshoturi, po.nDirectMessages,              self.ndirect),
                (self.snapshoturi, po.nUserMentions,              self.nmention),
                (self.snapshoturi, po.nCharsOverall, self.totalchars),
                (self.snapshoturi, po.mCharsOverall, self.mcharsmessages),
                (self.snapshoturi, po.dCharsOverall, self.dcharsmessages),
                (self.snapshoturi, po.nTokensOverall, self.totaltokens),
                (self.snapshoturi, po.mTokensOverall, self.mtokensmessages),
                (self.snapshoturi, po.dTokensOverall, self.dtokensmessages),
                ]
        P.add(triples,context=self.meta_graph)
        P.rdf.triplesScaffolding(self.snapshoturi,
                [po.ircParticipantAttribute]*len(self.participantvars),
                self.participantvars,context=self.meta_graph)
        P.rdf.triplesScaffolding(self.snapshoturi,
                [po.logXMLFilename]*len(self.log_rdf)+[po.logTTLFilename]*len(self.log_ttl),
                self.log_rdf+self.log_ttl,context=self.meta_graph)
        P.rdf.triplesScaffolding(self.snapshoturi,
                [po.onlineTweetXMLFile]*len(self.tweet_rdf)+[po.onlineTweetTTLFile]*len(self.tweet_ttl),
                [self.online_prefix+i for i in self.tweet_rdf+self.tweet_ttl],context=self.meta_graph)

        self.mrdf=self.snapshotid+"Meta.rdf"
        self.mttl=self.snapshotid+"Meta.ttl"
        self.desc="twitter dataset with snapshotID: {}\nsnapshotURI: {} \nisEgo: {}. isGroup: {}.".format(
                                                self.snapshotid,self.snapshoturi,self.isego,self.isgroup,)
        self.desc+="\nisFriendship: {}; ".format(self.isfriendship)
        self.desc+="isInteraction: {}.".format(self.isinteraction)
        self.desc+="\nnParticipants: {}; nInteractions: {} (responses+retweets+user mentions).".format(self.nparticipants,self.nreplies+self.nretweets+self.nuser_mentions,)
        self.desc+="\nisPost: {} (alias hasText: {})".format(self.hastext,self.hastext)
        self.desc+="\nnTweets: {}; ".format(self.ntweets)
        self.desc+="nReplies: {}; nRetweets: {}; nUserMentions: {}.".format(self.nreplies,self.nretweets,self.nuser_mentions)
        self.desc+="\nnTokens: {}; mTokens: {}; dTokens: {};".format(self.totaltokens,self.mtokenstweets,self.dtokenstweets)
        self.desc+="\nnChars: {}; mChars: {}; dChars: {}.".format(self.totalchars,self.mcharstweets,self.dcharstweets)
        self.desc+="\nnHashtags: {}; nMedia: {}; nLinks: {}.".format(self.nhashtags,self.nmedia,self.nlinks)
        triples=[
                (self.snapshoturi, po.triplifiedIn,      datetime.datetime.now()),
                (self.snapshoturi, po.triplifiedBy,      "scripts/"),
                (self.snapshoturi, po.donatedBy,         self.snapshotid[:-4]),
                (self.snapshoturi, po.availableAt,       self.online_prefix),
                (self.snapshoturi, po.onlineMetaXMLFile, self.online_prefix+self.mrdf),
                (self.snapshoturi, po.onlineMetaTTLFile, self.online_prefix+self.mttl),
                (self.snapshoturi, po.metaXMLFileName,   self.mrdf),
                (self.snapshoturi, po.metaTTLFileName,   self.mttl),
                (self.snapshoturi, po.totalXMLFileSizeMB, sum(self.size_rdf)),
                (self.snapshoturi, po.totalTTLFileSizeMB, sum(self.size_ttl)),
                (self.snapshoturi, po.acquiredThrough,   "Twitter APIs"),
                (self.snapshoturi, po.socialProtocolTag, "Twitter"),
                (self.snapshoturi, po.socialProtocol,    P.rdf.ic(po.Platform,"Twitter",self.meta_graph,self.snapshoturi)),
                (self.snapshoturi, po.nTriples,         self.ntriples),
                (self.snapshoturi, NS.rdfs.comment,         self.desc),
                ]
        P.add(triples,self.meta_graph)

        pass
    def writeAllIRC(self):
        pass

strange="Ã¡","Ã ","Ã¢","Ã£","Ã¤","Ã©","Ã¨","Ãª","Ã«","Ã­","Ã¬","Ã®","Ã¯","Ã³","Ã²","Ã´","Ãµ","Ã¶","Ãº","Ã¹","Ã»","Ã¼","Ã§","Ã","Ã€","Ã‚","Ãƒ","Ã„","Ã‰","Ãˆ","ÃŠ","Ã‹","Ã","ÃŒ","ÃŽ","Ã","Ã“","Ã’","Ã”","Ã•","Ã–","Ãš","Ã™","Ã›","Ãœ","Ã‡","Ã"
correct="á", "à", "â", "ã", "ä", "é", "è", "ê", "ë", "í", "ì", "î", "ï", "ó", "ò", "ô", "õ", "ö", "ú", "ù", "û", "ü", "ç", "Á", "À", "Â", "Ã", "Ä", "É", "È", "Ê", "Ë", "Í", "Ì", "Î", "Ï", "Ó", "Ò", "Ô", "Õ", "Ö", "Ú", "Ù", "Û", "Ü", "Ç","Ú"
def textFix(string):
    # https://berseck.wordpress.com/2010/09/28/transformar-utf-8-para-acentos-iso-com-php/
    for st, co in zip(strange,correct):
        string=string.replace(st,co)
    return string


